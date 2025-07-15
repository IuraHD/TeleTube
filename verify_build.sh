#!/bin/bash

echo "[*] YouTube Downloader Bot v3.0 - Final Build Verification"
echo

echo "[i] Checking package structure..."
ERROR_COUNT=0

# Check core files
if [ ! -f "yt_downloader_bot.py" ]; then
    echo "[!] ERROR: Main bot file missing"
    ((ERROR_COUNT++))
fi

if [ ! -f "requirements.txt" ]; then
    echo "[!] ERROR: Requirements file missing"
    ((ERROR_COUNT++))
fi

if [ ! -f ".env.example" ]; then
    echo "[!] ERROR: Environment template missing"
    ((ERROR_COUNT++))
fi

# Check documentation
if [ ! -f "README.md" ]; then
    echo "[!] ERROR: README missing"
    ((ERROR_COUNT++))
fi

if [ ! -f "SETUP_GUIDE.md" ]; then
    echo "[!] ERROR: Setup guide missing"
    ((ERROR_COUNT++))
fi

if [ ! -f "PACKAGE_CONTENTS.md" ]; then
    echo "[!] ERROR: Package contents missing"
    ((ERROR_COUNT++))
fi

# Check scripts
if [ ! -f "setup.bat" ]; then
    echo "[!] ERROR: Windows setup script missing"
    ((ERROR_COUNT++))
fi

if [ ! -f "setup.sh" ]; then
    echo "[!] ERROR: Unix setup script missing"
    ((ERROR_COUNT++))
fi

if [ ! -f "run_with_local_api.bat" ]; then
    echo "[!] ERROR: Local API launcher (Windows) missing"
    ((ERROR_COUNT++))
fi

if [ ! -f "run_with_local_api.sh" ]; then
    echo "[!] ERROR: Local API launcher (Unix) missing"
    ((ERROR_COUNT++))
fi

if [ ! -f "run_without_local_api.bat" ]; then
    echo "[!] ERROR: Standard launcher (Windows) missing"
    ((ERROR_COUNT++))
fi

if [ ! -f "run_without_local_api.sh" ]; then
    echo "[!] ERROR: Standard launcher (Unix) missing"
    ((ERROR_COUNT++))
fi

if [ ! -f "start_local_api.sh" ]; then
    echo "[!] ERROR: API server launcher (Unix) missing"
    ((ERROR_COUNT++))
fi

# Check API server
if [ ! -d "api_server" ]; then
    echo "[!] ERROR: API server folder missing"
    ((ERROR_COUNT++))
else
    if [ ! -f "api_server/telegram-bot-api" ] && [ ! -f "api_server/telegram-bot-api.exe" ]; then
        echo "[!] ERROR: Telegram Bot API executable missing"
        ((ERROR_COUNT++))
    fi
fi

# Check FFmpeg folder
if [ ! -d "ffmpeg" ]; then
    echo "[!] ERROR: FFmpeg folder missing"
    ((ERROR_COUNT++))
else
    if [ ! -f "ffmpeg/README.md" ]; then
        echo "[!] WARNING: FFmpeg README missing"
    fi
fi

# Check downloads folder
if [ ! -d "downloads" ]; then
    echo "[i] Creating downloads folder..."
    mkdir downloads
fi

echo
echo "[i] Package verification complete"
echo "[i] Error count: $ERROR_COUNT"

if [ $ERROR_COUNT -eq 0 ]; then
    echo "[+] Package structure is COMPLETE"
    echo "[+] Ready for distribution"
    echo
    echo "[i] Package features:"
    echo "    - Cross-platform support (Windows/Linux/Mac)"
    echo "    - Local Bot API server for 2GB file support"
    echo "    - FFmpeg integration for video processing"
    echo "    - GPU acceleration support"
    echo "    - Clean ASCII interface"
    echo "    - Comprehensive documentation"
    echo "    - Auto-start functionality"
    echo "    - Smart file handling"
    echo
    echo "[*] YouTube Downloader Bot v3.0 - READY FOR DEPLOYMENT"
else
    echo "[!] Package has $ERROR_COUNT missing components"
    echo "[!] Please fix these issues before distribution"
fi

echo
