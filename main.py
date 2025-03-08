import logging
import random
import threading
import time
from enum import Enum, auto
from pathlib import Path

import coloredlogs

from displayer import Displayer
from dreamer import Dreamer
from listener import Listener

coloredlogs.install(fmt='%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s')

logger = logging.getLogger(__name__)


class State(Enum):
    STARTUP = auto()
    LISTENING = auto()
    LOADING = auto()
    IMAGE = auto()


class Dreamscaper:

    def __init__(self):
        self._dreamer = Dreamer()
        self._listener = Listener()
        self._displayer = Displayer()
        self._app_running = threading.Event()
        self._displayer_lock = threading.Lock()
        self._last_image_ts = 0
        self._last_image_lock = threading.Lock()
        self._last_image = "assets/logo.jpeg"
        self._image_size = self.get_image_size()
        # State machine
        self._state = State.STARTUP
        self._state_lock = threading.Lock()

    def get_image_size(self):
        # Image size has to be such that the aspect ratio is maintained but the height is at default 1024
        screen_size = self._displayer.get_screen_size()
        aspect_ratio = screen_size[0] / screen_size[1]
        width = int(1024 * aspect_ratio / 16) * 16
        return width, 1024

    def on_demand_dream(self, timeout=5):
        while True:
            wake_word = self._listener.listen_for_wake()  # This is a blocking call

            # listen_for_wake was terminated
            if wake_word is None:
                logger.info(f"Terminating on-demand dream thread as listen_for_wake was terminated")
                break

            self.set_state(State.LISTENING)

            with self._displayer_lock:
                self._displayer.clear_screen()
                self._displayer.show_listening()

                dream_text = str()

                for dream_text in self._listener.listen_for_dream(timeout=timeout):
                    logger.info(f"dream_text = {dream_text}")
                    self._displayer.show_dream_prompt(dream_text)

                self._displayer.stop_show_listening()

                # No prompt was heard
                if not dream_text:
                    self._displayer.show_image(self._last_image)
                    self.set_state(State.IMAGE)
                    continue

                self._displayer.show_loading()
                self.set_state(State.LOADING)

                dream_img = self._dreamer.visualize(dream_text,
                                                    width=self._image_size[0],
                                                    height=self._image_size[1])

                self._displayer.stop_show_loading()

                if not dream_img:
                    self._displayer.show_message("Error generating image; Try again")
                    time.sleep(5)
                    self._displayer.show_image(self._last_image)
                    self.set_state(State.IMAGE)
                    continue

                self._displayer.show_image(dream_img)
                self.set_state(State.IMAGE)

            self.set_last_image_ts(time.time(), dream_img)

    def periodic_dream(self, period=86400):
        while True:
            dream_text = self._dreamer.imagine()
            dream_img = self._dreamer.visualize(dream_text,
                                                width=self._image_size[0],
                                                height=self._image_size[1])

            # If dream image could not be generated, choose a random one from the repo
            if not dream_img:
                dream_img = self.get_random_image_from_past()
                logger.info(f"Repeating dream {dream_img}")

            # Don't want to display an image if in on-demand mode
            # or if the last image was displayed less than `period` seconds ago
            while (self.get_state() in (State.LISTENING, State.LOADING)) or (
                    time.time() - self.get_last_image_ts() < period):
                time.sleep(1)

            with self._displayer_lock:
                self._displayer.show_image(dream_img)
                self.set_state(State.IMAGE)

            self.set_last_image_ts(time.time(), dream_img)

    @staticmethod
    def get_random_image_from_past():
        imgs = [f for f in Path("dreams").iterdir() if f.is_file()]

        if imgs:
            return random.choice(imgs)
        else:
            return "assets/logo.jpeg"

    def set_state(self, state):
        with self._state_lock:
            self._state = state
        logger.info(f"State set to {state}")

    def get_state(self):
        with self._state_lock:
            return self._state

    def set_last_image_ts(self, ts, image):
        with self._last_image_lock:
            self._last_image_ts = ts
            self._last_image = image
        logger.info(f"Last image was {image}\nDisplayed at {ts}")

    def get_last_image_ts(self):
        with self._last_image_lock:
            return self._last_image_ts

    def run(self):
        self._displayer.show_startup()

        listener_thread = threading.Thread(target=self.on_demand_dream,
                                           kwargs={"timeout": 5},
                                           daemon=True)
        listener_thread.start()

        dreamer_thread = threading.Thread(target=self.periodic_dream,
                                          kwargs={"period": 86400},
                                          daemon=True)
        dreamer_thread.start()

        try:
            self._displayer.run()  # This has to be part of main thread

        except Exception as e:
            logger.error(e)

        finally:
            self._listener.shutdown()
            self._displayer.shutdown()


if __name__ == "__main__":
    dreamscaper = Dreamscaper()
    dreamscaper.run()
