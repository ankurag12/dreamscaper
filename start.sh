#!/bin/bash

# This script is used to run the service in the background
# It is called by the AutoStart script
cd $HOME/dreamscaper
source ./.env/bin/activate
python main.py >> ./stdout.log 2>&1 &
