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

    def show_image(self, image_path="assets/logo.jpeg", size=None):
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

    def show_loading(self):
        """This is displayed while waiting for image to be generated"""
        # TODO: Make into animation
        self.show_image("assets/loading.png")

    def show_listening(self):
        """This is displayed as soon as the wake phrase is heard. It shows the voice prompt in real-time"""
        # TODO: Make into animation
        self.show_image("assets/mic.png")

    def run(self):
        # Main loop
        clock = pygame.time.Clock()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Quit event
                    running = False
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:  # Exit on ESC
                    running = False

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

    def clear_screen(self, color=None):
        if not color:
            color = self.BLACK

        # Fill the screen with a background color
        self._screen.fill(color)

    def show_startup(self):
        self.show_image("assets/logo.jpeg")

    @staticmethod
    def shutdown():
        # Quit Pygame
        # This can be called multiple times as repeated calls have no effect
        pygame.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()
