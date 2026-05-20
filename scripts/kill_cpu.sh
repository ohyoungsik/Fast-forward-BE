#!/bin/bash

pid=$(/usr/bin/pgrep stress | /usr/bin/head -1)

if [ -n "$pid" ]; then
  /usr/bin/pkill stress
  echo "Killing process stress (PID: $pid)"
else
  echo "No process above threshold"
fi
