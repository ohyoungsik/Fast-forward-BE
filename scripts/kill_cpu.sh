#!/bin/bash

pid=$(pgrep stress | head -1)

if [ -n "$pid" ]; then
  pkill stress
  echo "Killing process stress (PID: $pid)"
else
  echo "No process above threshold"
fi
