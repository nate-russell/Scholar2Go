import torch
import librosa
import time
import yaml
from argparse import Namespace
from espnet.asr.asr_utils import get_model_conf
from espnet.asr.asr_utils import torch_load
from espnet.utils.dynamic_import import dynamic_import
from tacotron_cleaner.cleaners import custom_english_cleaners
from g2p_en import G2p
import parallel_wavegan.models
import nltk

nltk.download('punkt')

trans_type = "phn"
dict_path = "/home/ntrusse2/espnet/downloads/en/fastspeech/data/lang_1phn/phn_train_no_dev_units.txt"
model_path = "/home/ntrusse2/espnet/downloads/en/fastspeech/exp/phn_train_no_dev_pytorch_train_tacotron2.v3_fastspeech.v4.single/results/model.last1.avg.best"
vocoder_path = "/home/ntrusse2/espnet/downloads/en/parallel_wavegan/ljspeech.parallel_wavegan.v2/checkpoint-400000steps.pkl"
vocoder_conf = "/home/ntrusse2/espnet/downloads/en/parallel_wavegan/ljspeech.parallel_wavegan.v2/config.yml"

device = torch.device("cuda")

print("Loading Torch Model...")
idim, odim, train_args = get_model_conf(model_path)
model_class = dynamic_import(train_args.model_module)
model = model_class(idim, odim, train_args)
torch_load(model_path, model)
model = model.eval().to(device)
inference_args = Namespace(**{
    "threshold": 0.5, "minlenratio": 0.0, "maxlenratio": 10.0,
    "use_attention_constraint": True,
    "backward_window": 1, "forward_window": 3,
})

print("Loading Vocoder...")
with open(vocoder_conf) as f:
    config = yaml.load(f, Loader=yaml.Loader)
vocoder_class = config.get("generator_type", "ParallelWaveGANGenerator")
vocoder = getattr(parallel_wavegan.models, vocoder_class)(**config["generator_params"])
vocoder.load_state_dict(torch.load(vocoder_path, map_location="cpu")["model"]["generator"])
vocoder.remove_weight_norm()
vocoder = vocoder.eval().to(device)

print("Loading Text Frontend...")
with open(dict_path) as f:
    lines = f.readlines()
lines = [line.replace("\n", "").split(" ") for line in lines]
char_to_id = {c: int(i) for c, i in lines}
g2p = G2p()


def frontend(text):
    """Clean text and then convert to id sequence."""
    text = custom_english_cleaners(text)
    if trans_type == "phn":
        text = filter(lambda s: s != " ", g2p(text))
        text = " ".join(text)
        print(f"Cleaned text: {text}")
        charseq = text.split(" ")
    else:
        print(f"Cleaned text: {text}")
        charseq = list(text)
    idseq = []
    for c in charseq:
        if c.isspace():
            idseq += [char_to_id["<space>"]]
        elif c not in char_to_id.keys():
            idseq += [char_to_id["<unk>"]]
        else:
            idseq += [char_to_id[c]]
    idseq += [idim - 1]  # <eos>
    return torch.LongTensor(idseq).view(-1).to(device)


input_text = """
n this work, we propose a new loss for supervised training which completely does away with a reference distribution; instead we simply impose that normalized embeddings from the same class are closer together than embeddings from different classes. Our loss is directly inspired by the family of contrastive objective functions, which have achieved excellent performance in self-supervised learning in recent years in the image and video domains <ref target="#b49" type="bibr">[50,</ref><ref target="#b24" type="bibr">25,</ref><ref target="#b20" type="bibr">21,</ref><ref target="#b18" type="bibr">19,</ref><ref target="#b45" type="bibr">46,</ref><ref target="#b5" type="bibr">6,</ref><ref target="#b42" type="bibr">43]</ref> and have connections to the large literature on metric learning <ref target="#b47" type="bibr">[48,</ref><ref target="#b4" type="bibr">5]</ref>.</p>

"""

pad_fn = torch.nn.ReplicationPad1d(
    config["generator_params"].get("aux_context_window", 0))
use_noise_input = vocoder_class == "ParallelWaveGANGenerator"
with torch.no_grad():
    start = time.time()
    print("Front End")
    x = frontend(input_text)
    print("Inference")
    c, _, _ = model.inference(x, inference_args)
    c = pad_fn(c.unsqueeze(0).transpose(2, 1)).to(device)
    xx = (c,)
    if use_noise_input:
        z_size = (1, 1, (c.size(2) - sum(pad_fn.padding)) * config["hop_size"])
        z = torch.randn(z_size).to(device)
        xx = (z,) + xx
    print("Vocoder")
    y = vocoder(*xx).view(-1)
rtf = (time.time() - start) / (len(y) / config["sampling_rate"])

print(f"RTF = {rtf:5f}")
librosa.output.write_wav('/home/ntrusse2/test.wav', y.view(-1).cpu().numpy(), config["sampling_rate"])

from pydub import AudioSegment

AudioSegment.from_wav('/home/ntrusse2/test.wav').export('/home/ntrusse2/test.mp3', format="mp3")

import eyed3

audiofile = eyed3.load('/home/ntrusse2/test.mp3')
audiofile.initTag()
'''
audiofile.tag.artist = self.authors
audiofile.tag.album = self.paper_identifier
audiofile.tag.album_artist = 'PDF2GO'
audiofile.tag.title = title
audiofile.tag.track_num = track_num
audiofile.tag.date = localtime().tm_year
'''

audiofile.tag.artist = "Scholar2Go"
audiofile.tag.album = "Free For All Comp LP"
audiofile.tag.album_artist = "Various Artists"
audiofile.tag.title = "The Edge"
audiofile.tag.track_num = 3

audiofile.tag.save()
'''

imagedata = open(self.cover_art, "rb").read()

# append image to tags
audiofile.tag.images.set(3, imagedata, "image/png", u"you can put a description here")

audiofile.tag.save()
'''
