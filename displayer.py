import logging
import os
import threading
import time
from collections import defaultdict

import pygame

logger = logging.getLogger(__name__)


class Displayer:
    # Define colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    def __init__(self):
        # Initialize Pygame
        pygame.init()

        # Set up the display
        self._screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Fullscreen mode
        self._screen_lock = threading.Lock()
        pygame.display.set_caption("Dreamscaper")

        # These are defaults that cannot be put in the kwargs
        self._defaults = {
            "size": (self._screen.get_width(), self._screen.get_height()),
            "center": (self._screen.get_width() // 2, self._screen.get_height() // 2),
        }

        self._app_running = threading.Event()

        # This keeps track of animations
        self._running_animations = defaultdict(threading.Event)
        self._running_animations_lock = threading.Lock()

        self._all_threads = list()

        self._dream_text_props = {
            "font_style": None,
            "font_size": self._screen.get_height() // 20,
            "font_color": (255, 255, 255),
            "center": (self._screen.get_width() // 2, self._screen.get_height() // 5)
        }

        self._dream_text_rect = pygame.Rect(0,
                                            self._dream_text_props["center"][1] - self._dream_text_props[
                                                "font_size"] // 2,
                                            self._screen.get_width(),
                                            self._dream_text_props["center"][1] + self._dream_text_props[
                                                "font_size"] // 2)

        self._mic_anim_props = {
            "sprite_sheet_path": "assets/mic_spritesheet.png",
            "animation_id": "listening",
            "num_frames": 78,
            "fps": 30,
            "size": (800, 447),  # TODO Make it scale by screen size
            "center": (self._screen.get_width() // 2, 2 * self._screen.get_height() // 3)
        }

        self._loading_anim_props = {
            "sprite_sheet_path": "assets/loading_spritesheet.png",
            "animation_id": "loading",
            "num_frames": 900,
            "fps": 50,
            "size": (512, 512),  # TODO Make it scale by screen size
            "center": (self._screen.get_width() // 2, 2 * self._screen.get_height() // 3)
        }

    def _get_defaults(self, **kwargs):
        ret = []
        for k, v in kwargs.items():
            if v is None:
                ret.append(self._defaults.get(k, v))
            else:
                ret.append(v)
        return tuple(ret)

    def show_image(self, image_path="assets/logo.jpeg", size=None, center=None):
        if not image_path or not os.path.exists(image_path):
            logger.error(f"Could not locate image at {image_path}")
            return

        # Load an image
        image = pygame.image.load(image_path)

        size, center = self._get_defaults(size=size, center=center)

        image = pygame.transform.scale(image, size)

        # Render the image
        image_rect = image.get_rect(center=center)
        with self._screen_lock:
            self._screen.blit(image, image_rect)

    def _show_text(self, text, font_style=None, font_size=75, font_color=(255, 255, 255), center=None):
        # Define a font
        font = pygame.font.Font(font_style, font_size)  # None uses the default font

        center = self._get_defaults(center=center)

        # Render the text
        text = font.render(text, True, font_color)

        text_rect = text.get_rect(center=center)

        with self._screen_lock:
            self._screen.blit(text, text_rect)

    def _show_animation(self, sprite_sheet_path, animation_id, num_frames, fps, size=None, center=None):
        """Displays animation using a sprite sheet made up of frames of a gif/video"""
        sprite_sheet = pygame.image.load(sprite_sheet_path)
        size, center = self._get_defaults(size=size, center=center)
        sprite_sheet = pygame.transform.scale(sprite_sheet, (size[0] * num_frames, size[1]))

        # Extract individual frames
        sprite_sheet_size = sprite_sheet.get_size()
        frame_width = sprite_sheet_size[0] // num_frames
        frame_height = sprite_sheet_size[1]
        frames = [sprite_sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)) for i in
                  range(num_frames)]

        frame_index = 0

        with self._running_animations_lock:
            self._running_animations[animation_id].set()

        while True:
            with self._running_animations_lock:
                if not self._running_animations[animation_id].is_set():
                    break
            frame = frames[frame_index % num_frames]
            with self._screen_lock:
                self._screen.blit(frame, frame.get_rect(center=center))
            t0 = time.time()
            while time.time() - t0 < 1 / fps:
                time.sleep(0.0001)
            frame_index += 1

    def show_loading(self):
        """This is displayed while waiting for image to be generated"""
        thread = threading.Thread(target=self._show_animation,
                                  kwargs=self._loading_anim_props,
                                  daemon=True)
        self._all_threads.append(thread)
        thread.start()

    def show_listening(self):
        """This is displayed as soon as the wake phrase is heard. It shows the voice prompt in real-time"""
        thread = threading.Thread(target=self._show_animation,
                                  kwargs=self._mic_anim_props,
                                  daemon=True)
        self._all_threads.append(thread)
        thread.start()

    def stop_show_listening(self):
        self._running_animations["listening"].clear()

    def stop_show_loading(self):
        self._running_animations["loading"].clear()

    def show_dream_prompt(self, dream_text):
        with self._screen_lock:
            pygame.draw.rect(self._screen, self.BLACK, self._dream_text_rect)

        self._show_text(dream_text,
                        **self._dream_text_props)

    def run(self):
        # Main loop
        clock = pygame.time.Clock()
        self._app_running.set()
        while self._app_running.is_set():
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Quit event
                    self._app_running.clear()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:  # Exit on ESC
                    self._app_running.clear()

            pygame.display.flip()
            clock.tick(60)

        self.shutdown()

    def clear_screen(self, color=None):
        if not color:
            color = self.BLACK

        # Fill the screen with a background color
        with self._screen_lock:
            self._screen.fill(color)

    def show_startup(self):
        self.show_image("assets/logo.jpeg")

    def shutdown(self):
        with self._running_animations_lock:
            for key in self._running_animations:
                self._running_animations[key].clear()
        # Quit Pygame
        # This can be called multiple times as repeated calls have no effect
        for th in self._all_threads:
            th.join()
        pygame.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
