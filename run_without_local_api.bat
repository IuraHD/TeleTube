@echo off

echo Starting YouTube Bot with Standard API...

:: Set environment variables for standard API
set USE_LOCAL_API=false
set MAX_FILE_SIZE_MB=50
echo Configuration set for standard API (50MB file limit)

echo Starting bot with Standard Telegram API...
call venv\Scripts\activate.bat
python yt_downloader_bot.py

pause
