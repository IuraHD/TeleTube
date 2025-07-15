@echo off

echo [*] Starting YouTube Bot with Local API Server...

:: Start the local API server first
echo [+] Starting Local Bot API Server...

:: Check if API server exists
if not exist "api_server\telegram-bot-api.exe" (
    echo [!] API server not found!
    echo [i] Expected: api_server\telegram-bot-api.exe
    echo [i] Please ensure the API server files are in the api_server folder
    pause
    exit /b 1
)

:: Load environment variables from .env file for API server
echo [i] Loading API credentials from .env file...
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="API_ID" set API_ID=%%b
    if "%%a"=="API_HASH" set API_HASH=%%b
)

:: Check if API credentials are set
if "%API_ID%"=="your_api_id_here" (
    echo [!] API_ID not configured!
    echo [i] Please edit .env file and set your API_ID from https://my.telegram.org/apps
    pause
    exit /b 1
)

if "%API_HASH%"=="your_api_hash_here" (
    echo [!] API_HASH not configured!
    echo [i] Please edit .env file and set your API_HASH from https://my.telegram.org/apps
    pause
    exit /b 1
)

echo [+] API credentials loaded
echo [*] Starting Local Bot API Server on port 8081...

:: Start the API server in background (non-blocking)
start "Local Bot API Server" /min cmd /c "cd api_server && telegram-bot-api.exe --api-id=%API_ID% --api-hash=%API_HASH% --http-port=8081 --local"

:: Wait a moment for server to initialize
echo [~] Waiting for server to initialize...
timeout /t 5 /nobreak >nul

:: Check if Local API is running
curl -s http://localhost:8081 >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ERROR: Local Bot API Server failed to start!
    echo [i] Please check your API credentials in .env file
    echo [i] Or use run_without_local_api.bat for standard API mode
    pause
    exit /b 1
)

echo [+] Local API detected, configuring for local server...

echo.
echo ===============================================================================
echo                              STARTING YOUTUBE BOT
echo ===============================================================================
echo.

:: Set environment variables for local API
set USE_LOCAL_API=true
set MAX_FILE_SIZE_MB=2000
echo [+] Configuration set for local API (2GB file limit)

echo [*] Starting bot with Local API...
call venv\Scripts\activate.bat
python yt_downloader_bot.py

pause
