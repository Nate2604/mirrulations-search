#!/bin/bash
set -euo pipefail

PID_FILE="gunicorn.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "No PID file found, have you run dev_up.sh"
  exit 1
fi

sudo kill -TERM "$(cat "$PID_FILE")"
rm -rf PID_FILE
echo "Mirralations Search is down"
