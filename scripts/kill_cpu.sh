#!/bin/bash

THRESHOLD=70

pid=$(pgrep stress | head -1)

if [ -n "$pid" ]; then

    cpu=$(ps -p $pid -o %cpu= | awk '{print int($1)}')

    if [ "$cpu" -ge "$THRESHOLD" ]; then
        pkill stress
        echo "Killed stress PID=$pid CPU=${cpu}%"
    else
        echo "Stress CPU ${cpu}% < ${THRESHOLD}%"
    fi

else
    echo "No stress process found"
fi