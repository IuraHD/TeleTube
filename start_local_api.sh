#!/bin/bash
# Local Bot API Server Starter (Linux/Mac)

echo "[*] Starting Local Bot API Server..."

# Check if API server exists
if [ ! -f "api_server/telegram-bot-api" ]; then
    echo "[!] API server not found!"
    echo "[i] Expected: api_server/telegram-bot-api"
    read -p "Press Enter to exit..."
    exit 1
fi

# Load environment variables from .env file
echo "[i] Loading configuration from .env file..."
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
echo "[i] Press Ctrl+C to stop the server"
echo ""

# Start the API server with credentials
cd api_server
./telegram-bot-api --api-id="$API_ID" --api-hash="$API_HASH" --http-port=8081 --local
