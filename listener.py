import logging
import time

import pvcheetah
import pvporcupine
from pvrecorder import PvRecorder

logging.basicConfig(level=logging.INFO)
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
            while self._porcupine_recorder.is_recording:
                pcm = self._porcupine_recorder.read()
                keyword_index = self._porcupine.process(pcm)

                # Wake phrase detected
                if keyword_index >= 0:
                    logger.info(f" Detected {self._wake_keywords[keyword_index]}")
                    self._porcupine_recorder.stop()
                    return self._wake_keywords[keyword_index]

        except Exception as e:
            logger.error(e)
            self._porcupine_recorder.stop()

    def listen_for_dream(self, timeout=5):
        self._cheetah_recorder.start()
        logger.info("Listening for dream...")

        is_endpoint = False
        t0 = time.time()
        cumulative_transcript = str()
        try:
            while not is_endpoint and self._cheetah_recorder.is_recording:
                pcm = self._cheetah_recorder.read()
                partial_transcript, is_endpoint = self._cheetah.process(pcm)
                cumulative_transcript += partial_transcript
                # We don't want it to be stuck here if no prompt is received
                if not cumulative_transcript and time.time() - t0 > timeout:
                    break

                if not partial_transcript:
                    continue

                logger.debug(f"cumulative_transcript = {cumulative_transcript}")

                yield cumulative_transcript

            if self._cheetah_recorder.is_recording:
                self._cheetah_recorder.stop()
            cumulative_transcript += self._cheetah.flush()
            logger.debug(f"cumulative_transcript = {cumulative_transcript}")

            yield cumulative_transcript

        except Exception as e:
            logger.error(f"Error raised while listening for dream: {e}")
            self._cheetah_recorder.stop()

    def shutdown(self):
        if self._porcupine_recorder.is_recording:
            self._porcupine_recorder.stop()
        self._porcupine_recorder.delete()

        if self._cheetah_recorder.is_recording:
            self._cheetah_recorder.stop()
        self._cheetah_recorder.delete()

        self._porcupine.delete()
        self._cheetah.delete()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
