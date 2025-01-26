from datetime import datetime

import pvcheetah
import pvporcupine
from pvrecorder import PvRecorder

keywords = ['picovoice', 'bumblebee']


class Listener:
    def __init__(self):
        self._pico_access_key = self._read_pico_access_key()

    @staticmethod
    def _read_pico_access_key():
        with open(".pico_access_key.txt", "r") as f:
            access_key = f.read()
        return access_key

    def run(self):
        pass


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

            image.show()

except KeyboardInterrupt:
    print('Stopping ...')
except Exception as e:
    print(e)

finally:
    recorder.delete()
    porcupine.delete()
    cheetah.delete()
