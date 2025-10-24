import logging
import os
import platform
import queue
import time
from contextlib import contextmanager
from ctypes import CFUNCTYPE, c_char_p, c_int, cdll

import numpy as np
import pvporcupine
import pyaudio
from google.cloud import speech
from openwakeword.model import Model
from pvrecorder import PvRecorder
import openwakeword


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

        # Initialize openWakeWord as backup wake word detection
        # Available wake words: "hey_jarvis", "alexa", "hey_mycroft", "hey_rhasspy"
        # inference_framework options:
        #   - 'onnx' (recommended): Lightweight, works on all platforms, faster startup
        #   - 'tflite': Uses TensorFlow Lite, larger but more compatible with TF ecosystem
        try:
            logger.info("Initializing openWakeWord (backup wake word detection)...")
            openwakeword.utils.download_models()
            self._oww_model = Model(
                wakeword_models=["hey_jarvis"],
                inference_framework='onnx'  # 'onnx' (recommended) or 'tflite'
            )
            self._oww_last_detection_time = 0  # For debouncing across calls
            logger.info("openWakeWord initialized successfully with 'hey jarvis' model")
        except Exception as e:
            logger.error(f"Could not initialize openWakeWord: {e}")
            self._oww_model = None

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

    def _listen_for_oww(self):
        """Listen for 'hey jarvis' wake word using openWakeWord with PvRecorder"""
        if not self._oww_model:
            return None

        # Reset model state to clear any cached audio from previous detections
        self._oww_model.reset()

        logger.info(f"Listening for 'hey jarvis' using openWakeWord... (last detection: {self._oww_last_detection_time})")

        # openWakeWord needs 1280 samples per chunk (80ms at 16kHz)
        # PvRecorder frame_length will be 512 by default, so we'll accumulate frames
        frame_length = 512
        oww_chunk_size = 1280  # 80ms at 16kHz
        debounce_time = 5.0  # Ignore detections for 5 seconds after first detection

        try:
            recorder = PvRecorder(frame_length=frame_length)
            recorder.start()

            audio_buffer = np.array([], dtype=np.int16)

            while recorder.is_recording:
                pcm = recorder.read()

                # Accumulate audio frames
                audio_buffer = np.append(audio_buffer, pcm)

                # Process when we have enough samples for openWakeWord
                if len(audio_buffer) >= oww_chunk_size:
                    # Take exactly oww_chunk_size samples
                    audio_chunk = audio_buffer[:oww_chunk_size]
                    audio_buffer = audio_buffer[oww_chunk_size:]

                    # Get predictions from openWakeWord
                    prediction = self._oww_model.predict(audio_chunk)

                    # Check if wake word detected
                    for wake_word, score in prediction.items():
                        # Log scores periodically for debugging (every 100 chunks)
                        if np.random.rand() < 0.01:  # ~1% of the time
                            logger.debug(f"'{wake_word}' score: {score:.3f}")

                        if score > 0.5:  # Detection threshold
                            current_time = time.time()
                            time_since_last = current_time - self._oww_last_detection_time

                            # Check debounce - ignore if detected recently
                            if time_since_last < debounce_time:
                                logger.info(f"Ignoring duplicate detection (debounce: {time_since_last:.1f}s < {debounce_time}s)")
                                continue

                            logger.info(f"Detected '{wake_word}' (confidence: {score:.2f})")
                            logger.info(f"Setting debounce timer to {current_time}")
                            self._oww_last_detection_time = current_time  # Update debounce timer
                            recorder.stop()
                            recorder.delete()
                            return wake_word

        except Exception as e:
            logger.error(f"Error in openWakeWord detection: {e}")
            if recorder and recorder.is_recording:
                recorder.stop()
            if recorder:
                recorder.delete()
            return None

    def listen_for_wake(self):
        if self._porcupine and self._porcupine_recorder:
            result = self._listen_for_wake_phrase()
            if result:
                return result

        return self._listen_for_oww()

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

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
