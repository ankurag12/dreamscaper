import logging
import os
import platform
import queue
import time
from contextlib import contextmanager
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll

import pvporcupine
import pyaudio
from clapDetector import ClapDetector
from google.cloud import speech
from pvrecorder import PvRecorder


# Used in the context manager to disable ALSA errors
c_error_handler = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)(
    lambda filename, line, function, err, fmt: None)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# This class is straight up taken from Google's example
# https://cloud.google.com/speech-to-text/docs/samples/speech-transcribe-streaming-mic?hl=en#speech_transcribe_streaming_mic-python
class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self: object, rate: int = 16000, chunk: int = 1600) -> None:
        """The audio -- and generator -- is guaranteed to be on the main thread."""
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    @contextmanager
    def noalsaerr(self):
        """Disable ALSA errors on Linux only (ALSA doesn't exist on macOS)"""
        # Only try to suppress ALSA errors on Linux
        if platform.system() == 'Linux':
            try:
                asound = cdll.LoadLibrary('libasound.so')
                asound.snd_lib_error_set_handler(c_error_handler)
                yield
                asound.snd_lib_error_set_handler(None)
            except OSError:
                # If ALSA library can't be loaded, just proceed without error suppression
                yield
        else:
            # On macOS and other platforms, just proceed without ALSA error suppression
            yield

    def __enter__(self: object) -> object:
        # Disable ALSA errors (Linux only)
        with self.noalsaerr():
            self._audio_interface = pyaudio.PyAudio()

        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            # The API currently only supports 1-channel (mono) audio
            # https://goo.gl/z757pE
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            # Run the audio stream asynchronously to fill the buffer object.
            # This is necessary so that the input device's buffer doesn't
            # overflow while the calling thread makes network requests, etc.
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(
            self: object,
            type: object,
            value: object,
            traceback: object,
    ) -> None:
        """Closes the stream, regardless of whether the connection was lost or not."""
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        # Signal the generator to terminate so that the client's
        # streaming_recognize method will not block the process termination.
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(
            self: object,
            in_data: object,
            frame_count: int,
            time_info: object,
            status_flags: object,
    ) -> object:
        """Continuously collect data from the audio stream, into the buffer.

        Args:
            in_data: The audio data as a bytes object
            frame_count: The number of frames captured
            time_info: The time information
            status_flags: The status flags

        Returns:
            The audio data as a bytes object
        """
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self: object) -> object:
        """Generates audio chunks from the stream of audio data in chunks.

        Args:
            self: The MicrophoneStream object

        Returns:
            A generator that outputs audio chunks.
        """
        while not self.closed:
            # Use a blocking get() to ensure there's at least one chunk of
            # data, and stop iteration if the chunk is None, indicating the
            # end of the audio stream.
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            # Now consume whatever other data's still buffered.
            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


class Listener:
    _wake_keywords = ['picovoice', 'bumblebee']

    def __init__(self):

        # PicoVoice for Wake word detection
        pico_access_key = self._read_pico_access_key()
        self._porcupine = None
        self._porcupine_recorder = None

        # Initialize clap detector with platform-appropriate device
        # Raspberry Pi optimized settings:
        # - exceptionOnOverflow=False: Prevents crashes when buffer overflows (common on RPi)
        # - bufferLength=4096: Larger buffer reduces read frequency and overflow risk
        self._clap_detector = ClapDetector(
            inputDevice=self._get_input_device(),
            logLevel=10,
            exceptionOnOverflow=False,  # Don't crash on buffer overflow
            bufferLength=4096           # Larger buffer for slower devices
        )
        self._clap_detector.initAudio()

        try:
            self._porcupine = pvporcupine.create(
                access_key=pico_access_key,
                keywords=Listener._wake_keywords,
                keyword_paths=["models/I-have-a-dream_en_raspberry-pi_v3_0_0.ppn"],
                sensitivities=[0.3]
            )
            self._porcupine_recorder = PvRecorder(frame_length=self._porcupine.frame_length)
        except Exception as e:
            logger.error(f"Could not initialize Porcupine {e}")

        # Google Cloud Speech-to-Text for Dream detection
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ".google-api-key.json"

        self._speech_client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US",
        )

        self._streaming_config = speech.StreamingRecognitionConfig(
            config=config,
            interim_results=True,
            single_utterance=True
        )

    @staticmethod
    def _find_usb_mic():
        """Find USB microphone device index by searching device names"""
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            # Look for USB device with input channels
            if 'USB' in info['name'] and info['maxInputChannels'] > 0:
                p.terminate()
                logger.info(f"Found USB microphone: {info['name']} at index {i}")
                return i
        p.terminate()
        return -1  # Fall back to default if not found

    @staticmethod
    def _get_input_device():
        """
        Get the appropriate input device for the current platform.
        On Raspberry Pi: Search for USB microphone
        On other systems: Use system default (-1)
        """
        if platform.machine() in ['armv7l', 'aarch64', 'armv6l']:
            # Raspberry Pi - search for USB mic
            input_device = Listener._find_usb_mic()
            if input_device == -1:
                logger.warning("USB microphone not found, using system default")
            return input_device
        else:
            # Mac or other systems - use default
            return -1

    @staticmethod
    def _read_pico_access_key():
        try:
            with open(".picovoice-key.txt", "r") as f:
                access_key = f.read()
        except FileNotFoundError:
            logger.error(f"Access key .picovoice-key.txt not found")
            access_key = None
        return access_key

    def _listen_for_wake_phrase(self):
        if not self._porcupine_recorder:
            return None

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
            if self._porcupine_recorder:
                self._porcupine_recorder.stop()

        return None

    def _listen_for_claps(self, threshold_bias=6000, lowcut=200, highcut=3200):
        logger.info("Listening for claps...")

        try:
            while True:
                audioData = self._clap_detector.getAudio()

                # Check if we have valid audio data
                if audioData is None or len(audioData) == 0:
                    time.sleep(1/60)
                    continue

                result = self._clap_detector.run(thresholdBias=threshold_bias, lowcut=lowcut, highcut=highcut, audioData=audioData)
                result_length = len(result)
                if result_length >= 2:
                    logger.debug(f"Multiple claps detected! bias {threshold_bias}, lowcut {lowcut}, and highcut {highcut}")
                    return result_length
                time.sleep(1/60)

        except Exception as e:
            logger.error(f"Error in clap detection: {e}")
            if self._clap_detector:
                self._clap_detector.stop()
            return None

    def listen_for_wake(self):
        if self._porcupine and self._porcupine_recorder:
            result = self._listen_for_wake_phrase()
            if result:
                return result
            
        return self._listen_for_claps()

    def listen_for_dream(self):
        logger.info("Listening for dream...")
        with MicrophoneStream() as stream:
            audio_generator = stream.generator()

            requests = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator
            )

            responses = self._speech_client.streaming_recognize(self._streaming_config, requests)

            finalized_transcript = str()

            for response in responses:
                logger.info(f"Response from Google Cloud:\n{response}")
                if not response.results:
                    if response.speech_event_type == speech.StreamingRecognizeResponse.SpeechEventType.END_OF_SINGLE_UTTERANCE:
                        break
                    continue

                if not response.results[0].alternatives:
                    continue

                current_transcript = str()
                # We take transcription of the top alternative from all the results as some chunks might never be deemed "is_final".
                for result in response.results:
                    this_transcript = result.alternatives[0].transcript

                    if result.is_final:
                        finalized_transcript += this_transcript
                    else:
                        current_transcript += this_transcript

                full_transcript = finalized_transcript + " " + current_transcript
                yield full_transcript

    def shutdown(self):
        if self._porcupine_recorder and self._porcupine_recorder.is_recording:
            self._porcupine_recorder.stop()
        if self._porcupine_recorder:
            self._porcupine_recorder.delete()

        if self._porcupine:
            self._porcupine.delete()

        if self._clap_detector:
            self._clap_detector.stop()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
