import glob, os
from google.cloud import texttospeech
from collections import namedtuple
import subprocess
import json
import time
import codecs
import eyed3
from time import localtime
from PIL import Image, ImageDraw, ImageFont
import random

os.environ[
    "GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\licun\\PycharmProjects\\PDF2GO\\google-key\\PDF2GO-2651afe6223d.json"


class Document:

    def __init__(self, path, out_dir):
        self.original_path = path
        self.out_dir = out_dir
        self.content_dict = self.pdf_to_json(path)
        self.authors = ',  '.join([author_dict['name'] for author_dict in self.content_dict['authors']])
        self.cover_art = self.make_album_cover(os.path.join(self.out_dir, self.paper_identifier + ".png"))

        # Abstract
        print('Abstract')
        abstract_text = self.content_dict["abstractText"]
        abstract_ssml = self.text_to_ssml(abstract_text, "abstract")
        abstract_path = self.paper_identifier + ' - %d %s.mp3' % (0, "abstract")
        mp3_path = os.path.join(self.out_dir, abstract_path)
        self.synthesize_text(ssml=abstract_ssml, mp3_path=mp3_path)
        self.tag_mp3(mp3_path=mp3_path, title="abstract", track_num=0)

        # Sections
        for i, section in enumerate(self.content_dict["sections"]):
            try:
                section_header = section["heading"]
            except KeyError:
                section_header = "No Heading"
            print(section_header, i + 1)
            section_text = section["text"]
            section_ssml = self.text_to_ssml(section_text, section_header)
            section_path = self.paper_identifier + ' - %d %s.mp3' % (i + 1, section_header)
            mp3_path = os.path.join(self.out_dir, section_path)
            self.synthesize_text(ssml=section_ssml, mp3_path=mp3_path)
            self.tag_mp3(mp3_path=mp3_path, title=section_header, track_num=i + 1)

    def text_to_ssml(self, text, header):
        """ TODO """
        return header + ": " + text

    def __str__(self):
        print(self.content_dict["id"])
        print(self.content_dict["title"])
        print(self.content_dict["year"])
        print('-' * 20)
        print('Abstract')
        print('-' * 20)
        print()
        print(self.content_dict["abstractText"])
        for section in self.content_dict["sections"]:

            print('-' * 20)
            try:
                print(section['heading'])
            except KeyError:
                print('No Heading')
            print('-' * 20)
            print()
            print(section['text'])

        print('\nReferences:')
        for ref in self.content_dict["references"]:
            print(ref['title'], ref['authors'][-1])
        return None

    def pdf_to_json(self, pdf_path, verbose=True):
        """"""
        tmp_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "tmp.json")
        cmd = 'curl -v -H "Content-type: application/pdf" --data-binary @%s "http://scienceparse.allenai.org/v1" > %s' % \
              (pdf_path, tmp_path)
        if verbose:
            print(cmd)
        try:
            scienceparse_dict = json.load(codecs.open(filename=tmp_path, mode='r', encoding='utf-8'))
            os.path.dirname(os.path.realpath(__file__))
            self.paper_identifier = ' - '.join([str(scienceparse_dict[key]) for key in ['title', 'year']])
            json_path = os.path.join(self.out_dir, self.paper_identifier + ".json")
            with open(json_path, 'w') as outfile:
                json.dump(scienceparse_dict, outfile, indent=4)


        except FileNotFoundError as fnfe:
            print(fnfe)

        return scienceparse_dict

    def synthesize_text(self, ssml, mp3_path):
        """Synthesizes speech from the input string of text."""
        print("# of Characters: ", len(ssml))
        ssml = ssml[0:5000]

        client = texttospeech.TextToSpeechClient()
        input_text = texttospeech.types.SynthesisInput(ssml=ssml)

        # Note: the voice can also be specified by name.
        # Names of voices can be retrieved with client.list_voices().
        voice = texttospeech.types.VoiceSelectionParams(
            language_code='en-GB',
            name='en-GB-Wavenet-D'
            # ssml_gender=texttospeech.enums.SsmlVoiceGender.MALE
        )

        audio_config = texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.MP3)

        response = client.synthesize_speech(input_text, voice, audio_config)

        # The response's audio_content is binary.
        with open(mp3_path, 'wb') as out:
            out.write(response.audio_content)
            print('Audio content written to file "%s"' % mp3_path)

    def tag_mp3(self, mp3_path, title, track_num=1):
        """ """
        audiofile = eyed3.load(mp3_path)
        audiofile.initTag()

        audiofile.tag.artist = self.authors
        audiofile.tag.album = self.paper_identifier
        audiofile.tag.album_artist = 'PDF2GO'
        audiofile.tag.title = title
        audiofile.tag.track_num = track_num
        audiofile.tag.date = localtime().tm_year

        imagedata = open(self.cover_art, "rb").read()

        # append image to tags
        audiofile.tag.images.set(3, imagedata, "image/png", u"you can put a description here")

        audiofile.tag.save()

    def make_album_cover(self, img_path, font_path="C:\Windows\Fonts\calibril.ttf"):
        """ """
        max_width = 500
        max_height = max_width
        horizontal_margin = 10

        r = random.choice(range(56, 200))
        g = random.choice(range(56, 200))
        b = random.choice(range(56, 200))
        base = Image.new('RGBA', (max_width, max_height), color=(r, g, b, 256))

        # make a blank image for the text, initialized to transparent text color
        txt = Image.new('RGBA', base.size, (255, 255, 255, 0))
        fnt = ImageFont.truetype(font_path, 60)
        d = ImageDraw.Draw(txt)

        paper_title = self.paper_identifier + ' by ' + self.authors

        # Determine where to put the breaks
        chunks = []
        words_list = paper_title.split(' ')
        last_length = 0
        start_index = 0
        for index in range(len(words_list)):
            line_text = ' '.join(words_list[start_index:index])
            new_length = fnt.getsize(line_text)[0]
            if new_length > max_width - (2 * horizontal_margin):
                start_index = index - 1
                chunks.append(index - 1)
        chunks.append(len(words_list))

        # Draw the Text
        vertical_position = 10
        start_index = 0
        for chunk in chunks:
            text = ' '.join(words_list[start_index:chunk])
            start_index = chunk
            d.text((horizontal_margin, vertical_position), text, font=fnt, fill=(255, 255, 255, 256))
            vertical_position += fnt.getsize(text)[1]

        out = Image.alpha_composite(base, txt)

        out.save(img_path)
        return img_path

    @property
    def ssml(self):
        return 'ssml'

    def transform_references(self, text):
        return None

    def clean(self, text):
        return None


def pdf2go_service(in_directories, out_dir):
    """

    :param directories:
    :return:
    """
    # Fetch all existing Docs
    processed = set()

    # Look for New Docs
    for dir_path in in_directories:
        os.chdir(dir_path)
        for file in glob.glob("*.pdf"):
            if file not in processed:
                file_path = os.path.join(dir_path, file)
                print('File: ', file_path)
                doc = Document(file_path, out_dir)
                print(doc)
                print(doc.save(out_dir))

                print('Quiting Early')
                quit()


if __name__ == '__main__':
    test_path = os.path.dirname(os.path.realpath(__file__))
    pdf2go_service([os.path.join(test_path, "test_docs")], "C:\\Users\\licun\\Documents\\PDF2GO")
