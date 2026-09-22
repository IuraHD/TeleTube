@echo off
setlocal
cd /d "%~dp0"
set USE_LOCAL_API=true
if exist venv\Scripts\python.exe (venv\Scripts\python.exe yt_downloader_bot.py) else (py -3 yt_downloader_bot.py)
