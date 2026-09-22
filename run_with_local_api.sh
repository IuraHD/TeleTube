#!/bin/sh
set -eu
cd "$(dirname "$0")"
export USE_LOCAL_API=true
if [ -x venv/bin/python ]; then exec venv/bin/python yt_downloader_bot.py; fi
exec python3 yt_downloader_bot.py
