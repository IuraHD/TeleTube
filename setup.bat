@echo off
setlocal
cd /d "%~dp0"
where ffmpeg >nul 2>nul || (echo Install FFmpeg and add it to PATH. & exit /b 1)
where ffprobe >nul 2>nul || (echo Install FFprobe and add it to PATH. & exit /b 1)
py -3 -m venv venv || exit /b 1
venv\Scripts\python.exe -m pip install -r requirements.txt || exit /b 1
if not exist .env copy .env.example .env >nul
echo Set TELEGRAM_BOT_TOKEN in .env, then run run_without_local_api.bat
