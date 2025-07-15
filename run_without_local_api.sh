#!/bin/bash
# YouTube Downloader Bot - Run without Local API (Linux/Mac) v3.0

echo "[*] Starting YouTube Bot with Standard API..."

# Set environment variables for standard API
export USE_LOCAL_API=false
export MAX_FILE_SIZE_MB=50
echo "[+] Configuration set for standard API (50MB file limit)"

echo "[*] Starting bot with Standard Telegram API..."
source venv/bin/activate
python yt_downloader_bot.py
