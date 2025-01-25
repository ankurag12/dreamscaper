import sys

import pygame


class Displayer:
    # Define colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)

    def __init__(self):
        # Initialize Pygame
        pygame.init()

        # Set up the display
        self._screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # Fullscreen mode
        pygame.display.set_caption("Dreamscaper")

    def show_image(self, image_path="cruise.jpeg", size=None):
        if size is None:
            size = (self._screen.get_width(), self._screen.get_height())

        # Load an image
        image = pygame.image.load(image_path)
        image = pygame.transform.scale(image, size)

        # Render the image
        image_rect = image.get_rect(center=(self._screen.get_width() // 2, self._screen.get_height() // 2))
        self._screen.blit(image, image_rect)

    def show_text(self, text, font_style=None, font_size=75):
        # Define a font
        font = pygame.font.Font(font_style, font_size)  # None uses the default font

        # Render the text
        text = font.render(text, True, self.WHITE)
        text_rect = text.get_rect(center=(self._screen.get_width() // 2, 100))  # Center the text
        self._screen.blit(text, text_rect)

    def show_loading(self, text=""):
        pass

    def run(self):
        # Main loop
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Quit event
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:  # Exit on ESC
                    running = False

            # Fill the screen with a background color
            self._screen.fill(self.BLACK)

            self.show_image()
            self.show_text("Hello")

            # Update the display
            pygame.display.flip()

    def shutdown(self):
        # Quit Pygame
        pygame.quit()
        sys.exit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


if __name__ == "__main__":
    displayer = Displayer()
    displayer.run()
