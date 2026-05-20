#!/bin/bash

pids=$(pgrep -f "stress|stress-ng")

if [ -z "$pids" ]; then
  echo "No stress process found"
  exit 0
fi

echo "Found stress process:"
ps -fp $pids

sudo -n pkill -f "stress|stress-ng"

if [ $? -eq 0 ]; then
  echo "Killed stress"
  exit 0
else
  echo "Failed to kill stress. Permission denied or sudo not allowed."
  exit 1
fi