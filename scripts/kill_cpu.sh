#!/bin/bash

THRESHOLD=50

# CPU 사용률이 높은 프로세스 중 가장 상위 하나를 찾음
top_process=$(ps -eo pid,comm,%cpu --sort=-%cpu | awk -v threshold=$THRESHOLD 'NR>1 && $3 > threshold {print $1, $2, $3; exit}')

if [ -n "$top_process" ]; then
  pid=$(echo $top_process | awk '{print $1}')
  comm=$(echo $top_process | awk '{print $2}')
  cpu=$(echo $top_process | awk '{print $3}')

  echo "$(date): Attempting to terminate process $comm (PID: $pid) using $cpu% CPU"

  # 먼저 SIGTERM으로 종료 시도
  kill -15 $pid
  sleep 2

  # 아직 살아있으면 SIGKILL로 강제 종료
  if ps -p $pid > /dev/null; then
    echo "$(date): Process $comm (PID: $pid) did not terminate, sending SIGKILL"
    kill -9 $pid
  else
    echo "$(date): Process $comm (PID: $pid) terminated gracefully"
  fi
else
  echo "$(date): No process above $THRESHOLD% CPU"
fi
