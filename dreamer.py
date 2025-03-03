import glob
import logging
import os.path
import random
from collections import OrderedDict

from huggingface_hub import InferenceClient

logger = logging.getLogger(__name__)


class Dreamer:

    def __init__(self):
        hf_token = self._read_hf_token()

        self._clients = OrderedDict({
            "Speed": InferenceClient("stabilityai/stable-diffusion-3.5-large-turbo", token=hf_token),
            "Balance": InferenceClient("stabilityai/stable-diffusion-3.5-large", token=hf_token),
            "Realistic": InferenceClient("black-forest-labs/FLUX.1-dev", token=hf_token),
            "Backup": InferenceClient("stable-diffusion-v1-5/stable-diffusion-v1-5", token=hf_token)
        })

        self._dream_prompts = self._read_dream_prompts()

    @staticmethod
    def _read_hf_token():
        with open(".hf_token.txt", "r") as f:
            token = f.read().strip()
        return token

    @staticmethod
    def _read_dream_prompts():
        files = glob.glob(os.path.join("prompts", "**", "*.txt"), recursive=True)
        dream_prompts = dict()
        for file in files:
            with open(file, "r") as f:
                dream_prompts[os.path.splitext(os.path.basename(file))[0]] = f.read().splitlines()
        return dream_prompts

    def visualize(self, text, quality=None, save_as=None, height=1024, width=1024):
        # Make a copy of the clients so that the original order is not disturbed and there's no contention between threads
        clients = self._clients.copy()
        # If quality is provided, give preference to that in the order of clients
        if quality:
            clients.move_to_end(quality, last=False)

        image = None
        for quality, client in clients.items():
            logger.info(f"Pinging HF.\nModel: {client}\nPrompt: {text}")
            try:
                image = clients[quality].text_to_image(text, height=height, width=width)
            except Exception as e:
                logger.error(f"{e} raised while trying to use {client}; will try a different model")
                continue
            break

        if not image:
            logger.error(f"Image could not be generated")
            return

        if not save_as:
            save_as = os.path.join("dreams", f"{text[:256]}.jpeg")

        os.makedirs(os.path.dirname(save_as), exist_ok=True)
        image.save(save_as)
        logger.info(f"Image saved as {save_as}")
        return save_as

    def imagine(self):
        """This generates prompt for a new dream using combination of random subject-activity"""
        dream = " ".join([random.choice(self._dream_prompts["adjectives"]),
                          random.choice(self._dream_prompts["subjects"]),
                          random.choice(self._dream_prompts["actions"])])
        return dream
