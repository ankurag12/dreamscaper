import logging
import time
import queue
import os
from google.cloud import speech
from pvrecorder import PvRecorder
import pyaudio
import pvporcupine


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

    def __enter__(self: object) -> object:
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

        self._porcupine = pvporcupine.create(
            access_key=pico_access_key,
            keywords=Listener._wake_keywords,
            keyword_paths=["models/I-have-a-dream_en_raspberry-pi_v3_0_0.ppn"]
        )

        self._porcupine_recorder = PvRecorder(frame_length=self._porcupine.frame_length)
        
        # Google Cloud Speech-to-Text for Dream detection
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = ".google-api-key.json"

        self._speech_client = speech.SpeechClient()
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="en-US" ,
        )

        self._streaming_config = speech.StreamingRecognitionConfig(
            config=config, 
            interim_results=True,
            single_utterance=True   # Not sure about this
        )

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
        
        logger.info("Listening for dream...")
        with MicrophoneStream() as stream:
            audio_generator = stream.generator()

            requests = (
                speech.StreamingRecognizeRequest(audio_content=content)
                for content in audio_generator
            )

            responses = self._speech_client.streaming_recognize(self._streaming_config, requests)

            # TODO: This is a blocking call. We need to make it non-blocking by addding a timeout            
            for response in responses:
                if not response.results:
                    continue

                # The `results` list is consecutive. For streaming, we only care about
                # the first result being considered, since once it's `is_final`, it
                # moves on to considering the next utterance.
                result = response.results[0]
                if not result.alternatives:
                    continue

                # Display the transcription of the top alternative.
                transcript = result.alternatives[0].transcript

                yield transcript

                if result.is_final:
                    break

    def shutdown(self):
        if self._porcupine_recorder.is_recording:
            self._porcupine_recorder.stop()
        self._porcupine_recorder.delete()

        self._porcupine.delete()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
