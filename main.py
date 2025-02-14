import logging
import threading
import time

import coloredlogs

from displayer import Displayer
from dreamer import Dreamer
from listener import Listener

coloredlogs.install(fmt='%(asctime)s %(name)s[%(process)d] %(levelname)s %(message)s')

logger = logging.getLogger(__name__)


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

    def get_image_size(self):
        # Image size has to be such that the aspect ratio is maintained but the height is at default 1024
        screen_size = self._displayer.get_screen_size()
        aspect_ratio = screen_size[0] / screen_size[1]
        width = int(1024 * aspect_ratio / 8) * 8
        return width, 1024

    def on_demand_dream(self, quality="Speed", timeout=5):
        while True:
            wake_word = self._listener.listen_for_wake()  # This is a blocking call

            # listen_for_wake was terminated
            if wake_word is None:
                logger.info(f"Terminating on-demand dream thread as listen_for_wake was terminated")
                break

            with self._displayer_lock:
                self._displayer.clear_screen()
                self._displayer.show_listening()
                dream_text = str()

                for dream_text in self._listener.listen_for_dream(timeout=timeout):
                    print(f"dream_text = {dream_text}")
                    self._displayer.show_dream_prompt(dream_text)

                self._displayer.stop_show_listening()

                # No prompt was heard
                if not dream_text:
                    self._displayer.show_image(self._last_image)
                    continue

                self._displayer.show_loading()
                # For better user experience of on-demand dream, choose a model that offers better speed
                dream_img = self._dreamer.visualize(dream_text,
                                                    quality=quality,
                                                    width=self._image_size[0],
                                                    height=self._image_size[1])

                self._displayer.stop_show_loading()
                self._displayer.show_image(dream_img)

            with self._last_image_lock:
                self._last_image_ts = time.time()
                self._last_image = dream_img

    def periodic_dream(self, quality="Realistic", period=86400):
        while True:
            dream_text = self._dreamer.imagine()
            # For periodic dreams, we can afford to use models that offer high quality at the cost of more time
            dream_img = self._dreamer.visualize(dream_text, quality=quality)

            # If there's a new on-demand dream displayed, we want to reset timer for period.
            # Hence, this complication instead of a simple time.sleep(period)
            # TODO: We also don't want to display an image if in on-demand mode
            while True:
                with self._last_image_lock:
                    dt = time.time() - self._last_image_ts
                if dt < period:
                    time.sleep(1)
                else:
                    break

            with self._displayer_lock:
                self._displayer.show_image(dream_img)

            with self._last_image_lock:
                self._last_image_ts = time.time()
                self._last_image = dream_img

    def run(self):
        self._displayer.show_startup()

        listener_thread = threading.Thread(target=self.on_demand_dream,
                                           kwargs={"quality": "Speed", "timeout": 5},
                                           daemon=True)
        listener_thread.start()

        dreamer_thread = threading.Thread(target=self.periodic_dream,
                                          kwargs={"quality": "Realistic", "period": 86400},
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
