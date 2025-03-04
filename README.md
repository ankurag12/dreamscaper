# dreamscaper

Voice activated digital art! 🗣🖼️️

It uses generative AI, so the art can be as imaginative as your dreams, hence the name!

Although I upcycled an old Macbook's display for this specific project, the code should work on any computer with a
display. More details on that part of the project on the [project page](https://ankurag12.github.io/dreamscaper/).

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

This project uses external APIs, which need an access key/token to use their service

- [Picovoice Porcupine](https://picovoice.ai/platform/porcupine/) for wake word detection (offline, on device
  processing).
- [Google Cloud Speech to Text API](https://cloud.google.com/speech-to-text/docs) for converting the "dream" audio
  prompt to text.
- [HuggingFace Inference API](https://huggingface.co/docs/api-inference/index) for converting the text to image.

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

#### HuggingFace Inference API

Sign up on [HuggingFace](https://huggingface.co/join). Copy your access token from profile settings and save to a file
named `.hf_token.txt` in the project root dir.
> 💡 As of this writing, HuggingFace provides 1000 images/day for free!

> ❗ Keep all these access keys secure. Do not share or upload them to publicly available repos. I have added these three
> files to `.gitignore` just so that they don't accidentally get pushed to GitHub

### Run

You can run the code either by calling `main.py` explicitly

```commandline
python main.py
```

or from included `start.sh` script which is useful when running on a remote like RPi as it sets up some
required env
variables and doesn't terminate when you quit SSH

```commandline
./start.sh
```

## Usage

Dreamscaper responds to wake phrase "_I have a dream_", after which the dream can be described.

For example: "_I have a dream, a cat is cooking in a garden with headphones on_"

