import glob
import logging
import os.path
import random

from inference_clients import HFInferenceClient, NebiusClient, TogetherClient

logger = logging.getLogger(__name__)


class Dreamer:
    # Priority order based on the cost to use FLUX-schnell as of 2025/03/07
    _client_priority_order = (
        TogetherClient,
        NebiusClient,
        HFInferenceClient,
    )

    def __init__(self):
        self._clients = self._initialize_clients()
        if not self._clients:
            raise Exception("No clients could be initialized")
        self._dream_prompts = self._read_dream_prompts()

    def _initialize_clients(self):
        clients = list()
        for client_class in self._client_priority_order:
            try:
                client = client_class()
                clients.append(client)
            except Exception as e:
                logger.error(f"Error initializing {client_class}: {e}")
                continue
        return clients

    @staticmethod
    def _read_dream_prompts():
        files = glob.glob(os.path.join("prompts", "**", "*.txt"), recursive=True)
        dream_prompts = dict()
        for file in files:
            with open(file, "r") as f:
                dream_prompts[os.path.splitext(os.path.basename(file))[0]] = f.read().splitlines()
        return dream_prompts

    def visualize(self, text, save_as=None, height=1024, width=1024):
        image = None
        for client in self._clients:
            logger.info(f"Pinging client: {client}\nPrompt: {text}")
            try:
                image = client.text_to_image(text, height=height, width=width)
            except Exception as e:
                logger.error(f"{e} raised while trying to use {client}; will try next client")
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
                          random.choice(self._dream_prompts["actions"]),
                          random.choice(self._dream_prompts["objects"]),
                          random.choice(self._dream_prompts["places"])])
        return dream
