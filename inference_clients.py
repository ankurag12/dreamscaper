from huggingface_hub import InferenceClient
from together import Together
import base64
from PIL import Image
from io import BytesIO
from openai import OpenAI

class InferenceClient:
    def __init__(self, api_key=None):
        if api_key is None:
            api_key = self.read_token()

    def text_to_image(self, text, height=1024, width=1024):
        raise NotImplementedError
    
    def read_token(self):
        with open(self.default_api_key_path(), "r") as f:
            token = f.read().strip()
        return token
    
    @classmethod
    def default_api_key_path(cls):
        raise NotImplementedError
    

class HFInferenceClient(InferenceClient):
    def __init__(self, provider="hf-inference", api_key=None):
        super().__init__(api_key=api_key)
        self._client = InferenceClient(provider=provider, api_key=api_key)
        
    def text_to_image(self, text, model="black-forest-labs/FLUX.1-schnell", height=1024, width=1024):
        image = self._client.text_to_image(text, 
                                           model=model, 
                                           height=height, 
                                           width=width)
        return image
    
    @classmethod
    def default_api_key_path(cls):
        return ".hf_token.txt"
    
class TogetherClient(InferenceClient):
    def __init__(self, api_key=None):
        super().__init__(api_key=api_key)
        self._client = Together(api_key=api_key)

    def text_to_image(self, text, model="black-forest-labs/FLUX.1-schnell-free", height=1024, width=1024):
        response = self._client.images.generate(prompt=text, 
                                                model=model, 
                                                height=height, 
                                                width=width, 
                                                response_format="b64_json",
                                                steps=4)
        data = base64.b64decode(response.data[0].b64_json)
        image = Image.open(BytesIO(data))
        return image

    @classmethod
    def default_api_key_path(cls):
        return ".together-ai-key.txt"
    
class NebiusClient(InferenceClient):
    def __init__(self, api_key=None):
        super().__init__(api_key=api_key)
        self._client = OpenAI(base_url="https://api.studio.nebius.com/v1/", 
                              api_key=api_key)
        
    def text_to_image(self, text, model="black-forest-labs/flux-schnell", height=1024, width=1024):
        response = self._client.images.generate(
            model=model,
            response_format="b64_json",
            extra_body={
                "width": width,
                "height": height,
                "num_inference_steps": 4,
            },
            prompt=text
        )
        data = base64.b64decode(response.data[0].b64_json)
        image = Image.open(BytesIO(data))
        image.show()
        return image
    
    @classmethod
    def default_api_key_path(cls):
        return ".nebius-key.txt"
    

