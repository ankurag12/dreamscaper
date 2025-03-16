---
layout: default
title: Dreamscaper
description: Digital art from voice prompt 🗣🖼️️ <br> (& randomly constructed sentence)
---

# Dreamscaper

Dreamscaper responds to wake phrase "_I have a dream_", after which a dream to be visualized can be described.

For example: "_I have a dream, a cat is cooking in a garden with headphones on_"

It uses generative AI, so the art can be as imaginative as your dreams, hence the name!

In addition to generating images in response to a voice prompt, Dreamscaper also generates a new image every day from a prompt constructed with random combination of various part of a phrase ("subject", "object", "actions", etc.). 

## Motivation

I had a very old Macbook which was rendered useless after a water spill event. Looking for ideas on what to do with it (
other than tossing it in 🗑️), I was inspired by [this video](https://www.youtube.com/watch?v=CfirQC99xPc)
from [DIY Perks](https://www.youtube.com/@DIYPerks) to salvage the display. However, instead of a simple secondary
monitor, I was more interested in transforming it into something that fulfills my love of Art-Tech intersection. I
thoroughly enjoyed working on my [Stoic Dashboard](https://github.com/ankurag12/epd-dashboard/tree/main) with an e-paper
display, but this time I had the vibrancy of full color LCD and a lot more processing power (the Raspberry Pi from
Stoic Dashboard's
server!). Using a bit of help from our [friend](https://chatgpt.com) with bouncing-off ideas, I finally converged to
this concept (and name) of Dreamscaper.

## Components

### Electronics

- [LCD Controller](https://www.ebay.com/itm/155734974671): Connects to the display via its LVDS cable on one end, and to
  a Raspberry Pi via HDMI on the other. Yes, it's that simple. If you're using a monitor or a TV then you don't need this.
- [Raspberry Pi](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/): Runs
  the [code](https://github.com/ankurag12/dreamscaper)
- [USB Microphone](https://www.amazon.com/dp/B0CNVZ27YH): I believe any USB microphone should work
- Power supplies: 12V 2.5A for the LCD controller, 5V 3A for the Raspberry Pi. One could use a buck converter for 12V->5V and use just the one power supply to clean-up wiring; I didn't as I already had the power supplies in my box of random stuff.

### Code 
<img src="dreamscaper.svg" width="600px" />

Dreams to be visualized are generated using a text-to-image Inference API like [Together AI](https://docs.together.ai/docs/introduction) / [Nebius](https://studio.nebius.com/playground) / [HuggingFace](https://huggingface.co/join). 

These text prompts are created in two ways:
- **Periodic dream:** A prompt is constructed using the words listed in the text files in [prompts](https://github.com/ankurag12/dreamscaper/tree/main/prompts). This runs once every 24 hours, so a new image is generated every day.
- **On-demand dream:** A prompt is provided via voice input, which is then converted to text using [Google Cloud](https://cloud.google.com) Speech-to-Text (STT). Does that mean it is always listening? Yes, BUT, the wake-phrase detection engine from [Picovoice](https://picovoice.ai/platform/porcupine/) runs on device, so until the words "I have a dream" are uttered, it doesn't send microphone stream to the cloud.

Since it uses external services like Picovoice, Google Cloud and Together AI, user will need to create an account on those services to obtain their access keys. More detais on how to setup the project (dependencies, access keys, etc.) are provided on project [README](https://github.com/ankurag12/dreamscaper).

The code is written in Python. It should work on any computer running Python with a display, for example your laptop or a Raspberry Pi connected to your TV. So you don't necessarily need to salvage the display from a laptop to see it an action!

### Frame

This part of the project might seem trivial or boring for some; however, for me, it was quite a learning experience and I thoroughly enjoyed it. Living in an apartment with little to no experience in woodworking, I had reservations about making the frame out of wood because of the presumption that it requires a garage space and investment in expensive tools. What I soon learned that it was actually fairly easy to do a small project like this with these tools/components totaling <$75.
- [1/4" x 2" Hobby Boards](https://www.homedepot.com/p/Weaber-1-4-in-x-2-in-x-4-ft-S4S-Poplar-Board-27402/207058967) There are various sizes and types of hardwood boards available at the local hardware store like HomeDepot. I used poplar for this project because I didn't know any better and it was the cheapest. The width of 2" worked well for what I was looking for, and I just needed to cut them to length using a hand saw.
- [Japanese Hand Saw](https://www.amazon.com/dp/B0BWDXZVPY) It's a little expensive at $25 compared to the usual $10 hand saws at hardware stores, especially for the size, but I was prioritizing finish of the cut over speed for this (and future projects).
- [C-clamp](https://www.homedepot.com/p/Husky-3-in-Drop-Forged-C-Clamp-97891/205132116) or any kind of woodworking clamp to clamp the board to any flat surface like an old table (or a step ladder in my case) for cutting.
- [Epoxy Glue](https://www.amazon.com/dp/B001Z3C3AG) or wood glue to glue the boards pieces together.
- [Sanding Sponge](https://www.amazon.com/dp/B08279QR75) of different grits; just sand papers should also work.
- [Danish Oil](https://www.amazon.com/dp/B00CECVM8Q) for finishing. It really popped out a nice shine in the wood without being glossy. A little patience is required as it needs 3 coats, each taking 6 hours to cure, but the end result was definitely worth it.


