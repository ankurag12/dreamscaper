import logging
import threading
import time

from displayer import Displayer
from dreamer import Dreamer
from listener import Listener

logger = logging.getLogger(__name__)


class Dreamscaper:
    def __init__(self):
        self._dreamer = Dreamer()
        self._listener = Listener()
        self._displayer = Displayer()
        self._on_demand_event = threading.Event()
        self._displayer_lock = threading.Lock()

    def on_demand_dream(self):
        while True:
            self._listener.listen_for_wake()  # This is a blocking call

            # self._on_demand_event.set()

            with self._displayer_lock:
                self._displayer.show_listening()
                dream_text = str()
                for part in self._listener.listen_for_dream():
                    dream_text += part
                    self._displayer.show_text(dream_text)
                self._displayer.show_loading()
                dream_img = self._dreamer.visualize(dream_text)
                self._displayer.show_image(dream_img)

                # self._on_demand_event.clear()

    def random_dream(self):
        while True:
            dream_text = self._dreamer.imagine()
            dream_img = self._dreamer.visualize(dream_text)
            with self._displayer_lock:
                self._displayer.show_image(dream_img)
            time.sleep(60 * 10)

    def run(self):
        self._displayer.show_startup()

        listener_thread = threading.Thread(target=self.on_demand_dream)
        listener_thread.start()

        dreamer_thread = threading.Thread(target=self.random_dream)
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
