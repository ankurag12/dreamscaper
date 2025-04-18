# dreamscaper

Digital art from voice prompt! 🗣🖼️️  
(& randomly constructed sentence)

It uses generative AI, so the art can be as imaginative as your dreams, hence the name!

Although I upcycled an old Macbook's display for this specific project, the code should work on any computer with a
display, like a RaspberryPi connected to your TV!
More details on different components of the project and demos are on the [project page](https://ankurag12.github.io/dreamscaper/).

## Setting up

### System dependencies

If using RaspberryPi, install missing dependencies

```
sudo apt update && sudo apt upgrade -y
sudo apt install -y libsdl2-image-dev libsdl2-ttf-2.0-0 python3-pyaudio portaudio19-dev flac
```

### Python dependencies

Clone the repo and set up a virtual env

```commandline
git clone git@github.com:ankurag12/dreamscaper.git
python3 -m venv .env
source ./.env/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### Access Keys

This project uses external services, which need an access key to use their API

- [Picovoice Porcupine](https://picovoice.ai/platform/porcupine/) for wake word detection (offline, on device processing).
- [Google Cloud Speech to Text API](https://cloud.google.com/speech-to-text/docs) for converting the "dream" audio
  prompt to text.
- [Together AI](https://docs.together.ai/docs/introduction) / [Nebius](https://studio.nebius.com/playground) / [HuggingFace](https://huggingface.co/join) for converting the text to image (inference).


#### Picovoice Porcupine

Sign up on [Picovoice](https://console.picovoice.ai/signup). Copy your Access key from Picovoice console and save to a
file
named `.pico_access_key.txt` in the project root dir.

> 💡 As of this writing, the Free account for hobbyists provides
> **1 active user** (machine) per machine. That means if you activate it on your computer for testing it out, you'll
> have to be inactive for 30 days before testing on another computer like RPi. So use it wisely!

#### Google Cloud API

Sign up on [Google Cloud](https://cloud.google.com). Copy your Access key json from Picovoice console and save to a file
named `.google-api-key.json` in the project root dir.
> 💡 As of this writing, Google provides 60min/month for free!

#### Inference API

The space of generative AI inference providers is evolving fast, and with it their pricing models. [HuggingFace](https://huggingface.co) went from 1000 images/day to just $0.10/month of free credits! Sign-up on one or more of the following, copy your access key from profile settings and save to a file named as mentioned in the project root dir.
- [Together AI](https://docs.together.ai/docs/introduction): `.together-ai-key.txt`
- [Nebius](https://studio.nebius.com/playground): `.nebius-key.txt`
- [HuggingFace](https://huggingface.co/join): `hf_token.txt`


> ❗ Keep all these access keys secure. Do not share or upload them to publicly available repos. These three files have been added to `.gitignore` just so that they don't accidentally get pushed to GitHub

## Running

Run the code either by calling `main.py` explicitly

```commandline
python main.py
```

or from included `start.sh` script which runs `main.py` in the background and saves logs to `stdout.log`.

```commandline
./start.sh
```

## Usage

Dreamscaper responds to wake phrase "_I have a dream_", after which the dream can be described.

For example: "_I have a dream, a cat is cooking in a garden with headphones on_"
<div style="text-align: center;">
  <img src="docs/cat_barbequing_with_headphones_on.jpg" alt="cat_barbequing_with_headphones_on" style="width: 50%;"/>
</div>
In addition to generating images in response to a voice prompt, Dreamscaper also generates a new image every day from a
prompt constructed with random combination of various part of a phrase ("subject", "object", "actions", etc.). These
parts are listed in their respective text files in `prompts` directory. The longer (and more creative) these lists are, the more unique combinations and interesting dreams there will be!

