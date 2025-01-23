from datetime import datetime

import pvcheetah
import pvporcupine
from huggingface_hub import InferenceClient
from pvrecorder import PvRecorder

keywords = ['picovoice', 'bumblebee']


def read_pico_access_key():
    with open(".pico_access_key.txt", "r") as f:
        access_key = f.read()
    return access_key


def read_hf_token():
    with open(".hf_token.txt", "r") as f:
        token = f.read()
    return token


pico_access_key = read_pico_access_key()
hf_token = read_hf_token()

clients = {
    "Speed": InferenceClient("stabilityai/stable-diffusion-3.5-large-turbo", token=hf_token),
    "Balance": InferenceClient("stabilityai/stable-diffusion-3.5-large", token=hf_token),
    "Realistic": InferenceClient("black-forest-labs/FLUX.1-dev", token=hf_token),
    "Backup": InferenceClient("stable-diffusion-v1-5/stable-diffusion-v1-5", token=hf_token)
}

porcupine = pvporcupine.create(
    access_key=pico_access_key,
    keywords=keywords
)

cheetah = pvcheetah.create(
    access_key=pico_access_key,
    endpoint_duration_sec=2)

recorder = PvRecorder(
    frame_length=porcupine.frame_length)

recorder.start()
print('Listening... (press Ctrl+C to stop)')

try:
    while True:
        pcm = recorder.read()
        keyword_index = porcupine.process(pcm)

        # Wake phrase detected
        if keyword_index >= 0:
            print(f"[{datetime.now()}] Detected {keywords[keyword_index]}")

            # Start listening for the dream
            is_endpoint = False
            dream = str()
            while not is_endpoint:
                partial_transcript, is_endpoint = cheetah.process(recorder.read())
                dream += partial_transcript

            dream += cheetah.flush()
            # Call image generator
            print(f"NEW DREAM: {dream}")
            print("Painting dream...")
            image = clients["Balance"].text_to_image(dream)
            image.show()

except KeyboardInterrupt:
    print('Stopping ...')
except Exception as e:
    print(e)

finally:
    recorder.delete()
    porcupine.delete()
    cheetah.delete()
