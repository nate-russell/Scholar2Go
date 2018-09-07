# PDF 2 GO
Scientific papers converted to audio files so I can listen to papers while I cook / clean / exercise.
It's going to skip out on math/diagrams/tables. Even if I could parse the math consistently, I couldn't understand it by just listening anyway. Hopefully the audio files sans math and diagrams are enough to get me the high level content so I know what to spend time on at the office.

# Pipeline
1. Populate Queue
    1. Collect PDFs saved to desktop/downloads/documents
    2. Collect PDFs saved via Google Keep
    3. Collect PDFs from Google Scholar Recommendations
2. Transform PDFs into JSONs with [ScienceParse](https://github.com/allenai/science-parse)
3. Clean and Transform JSON text into SSML
    - replace references with "See X by x` Y by y,..."
    - strip out spurious stuff like arxiv + date on side of paper
    - Spelling things out vs Saying them Phonetically
    - Figure out what is best way to handle math / algorithms
4. Transform SSML into MP3 with Google Text-to-Speech
5. Tag MP3 with album and track info for easy organization in music apps
6. Automatically upload to mobile device (just dump it in a synced library like with google music)
    -

# Set-up (TODO)
1. Use pip to set up dependencies
```
pip install requirements.txt
```
2. Set up your google [text-to-speach](https://cloud.google.com/text-to-speech/) API if you don't already have one
3. Save the json to the google-key directory, make sure its the only thing in there
4. run test.py, you should get an album of mp3 files of a the test paper

# Usage
## Single Use
You have a single paper you want to process via
#### Python
```python
 TODO
```
#### Command Line
```
TODO
```



## Continuous Usage
Just download the paper and let the code do the rest. The process starts when your computer does. It watches a few dir, looks for new PDFs, renames them (since most file names for pdfs of a pre-print server or online journal are just a bunch of numbers and i can never be bothered to type in the title), makes the auidofiles, puts them in a dir that syncs with your mobile device. Then when you're making breakfast or going on a bike ride, the papers you downloaded with the intention of reading are now ready for auditory consumption.
#### Windows


