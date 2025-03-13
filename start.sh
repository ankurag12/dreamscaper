#!/bin/bash

# This script is used to run the service in the background
# It is called by the AutoStart script
cd $HOME/dreamscaper
source ./.env/bin/activate
python main.py >> ./stdout.log 2>&1 &

# Run a background process to trim the log every day
while true; do
  sleep 86400
  tail -n 10000 stdout.log > stdout.tmp && mv stdout.tmp stdout.log
done &