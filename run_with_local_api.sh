#!/bin/bash
# YouTube Downloader Bot - Run with Local API (Linux/Mac) v3.0

echo "[*] Starting YouTube Bot with Local API Server..."

# Start the local API server first
echo "[+] Starting Local Bot API Server..."

# Check if API server exists
if [ ! -f "api_server/telegram-bot-api" ]; then
    echo "[!] API server not found!"
    echo "[i] Expected: api_server/telegram-bot-api"
    echo "[i] Please ensure the API server files are in the api_server folder"
    read -p "Press Enter to exit..."
    exit 1
fi

# Load environment variables from .env file for API server
echo "[i] Loading API credentials from .env file..."
if [ -f ".env" ]; then
    source .env
else
    echo "[!] .env file not found!"
    echo "[i] Please create .env file with your configuration"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check if API credentials are set
if [ "$API_ID" = "your_api_id_here" ] || [ -z "$API_ID" ]; then
    echo "[!] API_ID not configured!"
    echo "[i] Please edit .env file and set your API_ID from https://my.telegram.org/apps"
    read -p "Press Enter to exit..."
    exit 1
fi

if [ "$API_HASH" = "your_api_hash_here" ] || [ -z "$API_HASH" ]; then
    echo "[!] API_HASH not configured!"
    echo "[i] Please edit .env file and set your API_HASH from https://my.telegram.org/apps"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[+] API credentials loaded"
echo "[*] Starting Local Bot API Server on port 8081..."

# Start the API server in background (non-blocking)
cd api_server
nohup ./telegram-bot-api --api-id="$API_ID" --api-hash="$API_HASH" --http-port=8081 --local > /dev/null 2>&1 &
cd ..

# Wait a moment for server to initialize
echo "[~] Waiting for server to initialize..."
sleep 5

# Check if Local API is running
curl -s http://localhost:8081 >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "[!] ERROR: Local Bot API Server failed to start!"
    echo "[i] Please check your API credentials in .env file"
    echo "[i] Or use ./run_without_local_api.sh for standard API mode"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[+] Local API detected, configuring for local server..."

echo ""
echo "==============================================================================="
echo "                              STARTING YOUTUBE BOT"
echo "==============================================================================="
echo ""

# Set environment variables for local API
export USE_LOCAL_API=true
export MAX_FILE_SIZE_MB=2000
echo "[+] Configuration set for local API (2GB file limit)"

echo "[*] Starting bot with Local API..."
source venv/bin/activate
python yt_downloader_bot.py
