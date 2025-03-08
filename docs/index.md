---
layout: default
title: Dreamscaper
description: Voice activated digital art! 🗣🖼️️ <br> (+images generated from random combination of words)
---

# Dreamscaper

Dreamscaper responds to wake phrase "_I have a dream_", after which the dream can be described.

For example: "_I have a dream, a cat is cooking in a garden with headphones on_"

It uses generative AI, so the art can be as imaginative as your dreams, hence the name!

## Motivation

I had a very old Macbook which was rendered useless after a water spill event. Looking for ideas on what to do with it (
other than tossing it in 🗑️), I was inspired by [this video](https://www.youtube.com/watch?v=CfirQC99xPc)
from [DIY Perks](https://www.youtube.com/@DIYPerks) to salvage the display. However, instead of a simple secondary
monitor, I was more interested in transforming it into something that fulfills my love of Art-Tech intersection. I
thoroughly enjoyed working on my [Stoic Dashboard](https://github.com/ankurag12/epd-dashboard/tree/main) with an e-paper
display, but this time I had the vibrancy of full color LCD and a lot more processing power (the Raspberry Pi from
Stoic Dashboard's
server!). Using a bit of help from our [friend](https://chatgpt.com) with bouncing-off ideas, I finally converged to
this idea (and name) of Dreamscaper.

### Components

#### Electronics

- [LCD Controller](https://www.ebay.com/itm/155734974671): Connects to the display via its LVDS cable on one end, and to
  a Raspberry Pi via HDMI on the other. Yes, it's that simple.
- [Raspberry Pi](https://www.raspberrypi.com/products/raspberry-pi-4-model-b/): Runs
  the [code](https://github.com/ankurag12/dreamscaper)
- [USB Microphone](https://www.amazon.com/dp/B0CNVZ27YH): I believe any USB microphone should work
- Power supplies: 12V 2.5A for the LCD controller, 5V 3A for the Raspberry Pi. One could use a buck converter for
  12V->5V and use just the one power supply to clean-up wiring; I didn't as I already had the power supplies in my box
  of random stuff.