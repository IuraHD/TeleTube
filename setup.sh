#!/bin/sh
set -eu
cd "$(dirname "$0")"
command -v ffmpeg >/dev/null || { echo 'Install FFmpeg first.' >&2; exit 1; }
command -v ffprobe >/dev/null || { echo 'Install FFprobe first.' >&2; exit 1; }
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
if [ ! -f .env ]; then cp .env.example .env; fi
echo 'Set TELEGRAM_BOT_TOKEN in .env, then run ./run_without_local_api.sh'
