import torch
import librosa
import time
import yaml
import numpy as np
from argparse import Namespace
from espnet.asr.asr_utils import get_model_conf
from espnet.asr.asr_utils import torch_load
from espnet.utils.dynamic_import import dynamic_import
from tacotron_cleaner.cleaners import custom_english_cleaners
from g2p_en import G2p
import parallel_wavegan.models
import nltk
from pydub import AudioSegment
import matplotlib.pyplot as plt

nltk.download('punkt')


class TTS:

    def __init__(self):
        # TODO Move this into a config File, give option of different models
        self.trans_type = "phn"
        dict_path = "/home/ntrusse2/espnet/downloads/en/fastspeech/data/lang_1phn/phn_train_no_dev_units.txt"
        model_path = "/home/ntrusse2/espnet/downloads/en/fastspeech/exp/phn_train_no_dev_pytorch_train_tacotron2.v3_fastspeech.v4.single/results/model.last1.avg.best"
        vocoder_path = "/home/ntrusse2/espnet/downloads/en/parallel_wavegan/ljspeech.parallel_wavegan.v2/checkpoint-400000steps.pkl"
        vocoder_conf = "/home/ntrusse2/espnet/downloads/en/parallel_wavegan/ljspeech.parallel_wavegan.v2/config.yml"

        # Copied right out of the examples on ESPNETs DEMO
        self.device = torch.device("cuda")
        print("Loading Torch Model...")
        self.idim, odim, train_args = get_model_conf(model_path)
        model_class = dynamic_import(train_args.model_module)
        model = model_class(self.idim, odim, train_args)
        torch_load(model_path, model)
        self.model = model.eval().to(self.device)
        self.inference_args = Namespace(**{
            "threshold": 0.5, "minlenratio": 0.0, "maxlenratio": 10.0,
            "use_attention_constraint": True,
            "backward_window": 1, "forward_window": 3,
        })

        print("Loading Vocoder...")
        with open(vocoder_conf) as f:
            self.config = yaml.load(f, Loader=yaml.Loader)
        vocoder_class = self.config.get("generator_type", "ParallelWaveGANGenerator")
        vocoder = getattr(parallel_wavegan.models, vocoder_class)(**self.config["generator_params"])
        vocoder.load_state_dict(torch.load(vocoder_path, map_location="cpu")["model"]["generator"])
        vocoder.remove_weight_norm()
        self.vocoder = vocoder.eval().to(self.device)

        print("Loading Text Frontend...")
        with open(dict_path) as f:
            lines = f.readlines()
        lines = [line.replace("\n", "").split(" ") for line in lines]
        self.char_to_id = {c: int(i) for c, i in lines}
        self.g2p = G2p()

        self.pad_fn = torch.nn.ReplicationPad1d(self.config["generator_params"].get("aux_context_window", 0))
        self.use_noise_input = vocoder_class == "ParallelWaveGANGenerator"

    def frontend(self, text):
        """

        :param text:
        :return:
        """
        text = custom_english_cleaners(text)
        if self.trans_type == "phn":
            text = filter(lambda s: s != " ", self.g2p(text))
            text = " ".join(text)
            # print(f"Cleaned text: {text}")
            charseq = text.split(" ")
        else:
            # print(f"Cleaned text: {text}")
            charseq = list(text)
        idseq = []
        for c in charseq:
            if c.isspace():
                idseq += [self.char_to_id["<space>"]]
            elif c not in self.char_to_id.keys():
                print(f"{c} is unknown!")
                idseq += [self.char_to_id["<unk>"]]
            elif c == ',':
                idseq += [self.char_to_id[c]]
                # done in an attempt to create a longer pause after commas, unsure exactly how this works
                idseq += [self.char_to_id[c]]
            else:
                idseq += [self.char_to_id[c]]
        idseq += [self.idim - 1]  # <eos>
        return torch.LongTensor(idseq).view(-1).to(self.device)

    def chunk_text(self, s):
        # TODO make the Chunking more sophisticated
        d = ". "
        x = [e + d for e in s.split(d) if e]
        return x

    def text_to_wav(self, input_text, wav_path):
        """

        :param input_text:
        :param wav_path:
        :return:
        """
        assert isinstance(input_text, str)
        assert len(input_text) > 0

        waves = []
        text_chunks = self.chunk_text(input_text)
        interval = int(np.ceil(len(text_chunks) / 5))

        with torch.no_grad():
            for ci, chunk in enumerate(text_chunks):
                if (ci + 1) % interval == 0 or (ci + 1) == len(text_chunks):
                    print(f"TTS: {ci + 1}/{len(text_chunks)}")
                x = self.frontend(chunk)
                c, _, _ = self.model.inference(x, self.inference_args)
                c = self.pad_fn(c.unsqueeze(0).transpose(2, 1)).to(self.device)
                xx = (c,)
                if self.use_noise_input:
                    z_size = (1, 1, (c.size(2) - sum(self.pad_fn.padding)) * self.config["hop_size"])
                    z = torch.randn(z_size).to(self.device)
                    xx = (z,) + xx
                y = self.vocoder(*xx).view(-1)
                waves.append(y.view(-1).cpu().numpy())
                # waves.append(np.zeros(263168))

        wave_array = np.hstack(waves)
        """
        plt.figure(figsize=(20, 3))
        plt.plot(wave_array)
        plt.show()
        plt.savefig("/home/ntrusse2/waveform.png")
        """
        librosa.output.write_wav(wav_path, wave_array, self.config["sampling_rate"])
        return True


if __name__ == '__main__':

    test_inputs = [
        "Sally sold seashells by the seashore",
        "RNN, DNN, GAN, VAE, Transformer, ReLu, CNN, polymatroid, word2vec, node2vec, TSNE, UMAP, ESPNet, GROBID",
        "R N N, D N N, GAN, V A E, Transformer, Re Lu, C N N, polymatroid, word-2-vec, node-2-vec, TSNE, UMAP, E-S-P-Net, GROBID",
        "achiral, nucleophile, valence isomerisation, tautomer, hydroboration",
        "      Convert research papers into M-P-Threes so you can listen to papers while you're on the go! (Think Audio book,  but with an A-I Narrator)" \
        "Survey some papers while: Commuting, Cooking, Cleaning, Exercising, Waiting for a slow build process or model training. Load up the latest conference proceedings on to your mobile device and start listening to all the abstracts to find " \
        "something interesting OR Try listening to a whole paper while you cook dinner."

    ]

    tts = TTS()
    for index, s in enumerate(test_inputs):
        print("Working on Test input", index)
        wav_path = f'/home/ntrusse2/test {index}.wav'
        mp3_path = f'demo_resources/test {index}.mp3'
        tts.text_to_wav(s, wav_path)
        AudioSegment.from_wav(wav_path).export(mp3_path, format="mp3")
