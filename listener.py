import logging
from datetime import datetime

import pvcheetah
import pvporcupine
from pvrecorder import PvRecorder

logger = logging.getLogger(__name__)


class Listener:
    _wake_keywords = ['picovoice', 'bumblebee']

    def __init__(self):
        pico_access_key = self._read_pico_access_key()

        self._porcupine = pvporcupine.create(
            access_key=pico_access_key,
            keywords=Listener._wake_keywords
        )

        self._cheetah = pvcheetah.create(
            access_key=pico_access_key,
            endpoint_duration_sec=2)

        self._porcupine_recorder = PvRecorder(frame_length=self._porcupine.frame_length)
        self._cheetah_recorder = PvRecorder(frame_length=self._cheetah.frame_length)

    @staticmethod
    def _read_pico_access_key():
        with open(".pico_access_key.txt", "r") as f:
            access_key = f.read()
        return access_key

    def listen_for_wake(self):
        self._porcupine_recorder.start()
        logger.info("Listening for wake phrase...")

        try:
            while True:
                pcm = self._porcupine_recorder.read()
                keyword_index = self._porcupine.process(pcm)

                # Wake phrase detected
                if keyword_index >= 0:
                    logger.info(f"[{datetime.now()}] Detected {self._wake_keywords[keyword_index]}")
                    self._porcupine_recorder.stop()
                    self.listen_for_dream()
                    return self.listen_for_wake()

        except Exception as e:
            print(e)
            self._porcupine_recorder.delete()

    def listen_for_dream(self):
        self._cheetah_recorder.start()
        logger.info("Listening for dream...")

        is_endpoint = False
        dream = str()

        try:
            while not is_endpoint:
                pcm = self._porcupine_recorder.read()
                partial_transcript, is_endpoint = self._cheetah.process(pcm)
                dream += partial_transcript

            dream += self._cheetah.flush()
            self._cheetah_recorder.stop()

        except Exception as e:
            logger.error(e)
            self._porcupine_recorder.delete()

        return dream

    def shutdown(self):
        self._porcupine_recorder.delete()
        self._cheetah_recorder.delete()
        self._porcupine.delete()
        self._cheetah.delete()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
