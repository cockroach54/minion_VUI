"""
https://brunch.co.kr/@khross3701/4 - googlr speech recognition

"""

import io
import os
import subprocess
import base64

# Imports the Google Cloud client library
from google.cloud import speech
from google.cloud.speech import enums
from google.cloud.speech import types

# enviorment variable
os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="My First Project-cadf64234338.json"


# decode base64 -> webm
def base2webm(base64_, file_name='decode.webm'):
    assert type(base64_) is str
    # with io.open(base64_, 'rb') as ff:
    #     base64_bytes = ff.read()
    with io.open(file_name, 'wb') as f:
        f.write(base64.b64decode(base64_))
    return file_name

def webm2flac(webm_, file_name='temp.flac'):
    assert type(webm_) is str
    command = "ffmpeg -i {} -c:a flac -ar 16k -y {}".format(webm_, file_name)
    print(command)
    subprocess.call(command, shell=True)
    return file_name

def speech2text(flac_, bit_rate=16000):
    assert type(flac_) is str and bit_rate in [16000, 48000]
    client = speech.SpeechClient()
    with io.open(flac_, 'rb') as audio_file:
        content = audio_file.read()

    audio = types.RecognitionAudio(content=content)
    config = types.RecognitionConfig(
        encoding="FLAC",
        sample_rate_hertz=bit_rate,
        language_code='ko-KR')

    response = client.recognize(config, audio)
    texts=[]
    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    for result in response.results:
        # The first alternative is the most likely one for this portion.
        print('Transcript: {}'.format(result.alternatives[0].transcript))
        texts.append(result.alternatives[0].transcript.strip())
    return texts