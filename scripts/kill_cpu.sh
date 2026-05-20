#!/bin/bash

pids=$(/usr/bin/pgrep -f "stress")

if [ -z "$pids" ]; then
  echo "No stress process found"
  exit 0
fi

echo "Found stress process: $pids"

sudo -n /usr/bin/pkill -f "stress"

if [ $? -eq 0 ]; then
  echo "Killed stress"
  exit 0
else
  echo "Failed to kill stress. Permission denied or sudo not allowed."
  exit 1
fi
