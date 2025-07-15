@echo off
titl::⁣ Check if Python is installed
echo 📋 Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found!
    echo.
    echo 📥 Please install Python 3.11.0 first:
    echo    1. Go to https://python.org/downloads/
    echo    2. Download Python 3.11.0 specifically
    echo    3. IMPORTANT: Check "Add Python to PATH" during installation
    echo    4. Restart this setup after Python installation
    echo.
    pause
    exit /b 1
)

:: Check Python version - require 3.11.0
echo 📋 Verifying Python version...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python found: %PYTHON_VERSION%

:: Extract major.minor version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if not "%PYTHON_MAJOR%.%PYTHON_MINOR%"=="3.11" (
    echo ⚠️  Python version mismatch!
    echo.
    echo ❌ Required: Python 3.11.0
    echo ❌ Found:    Python %PYTHON_VERSION%
    echo.
    echo 📥 Please install Python 3.11.0:
    echo    1. Go to https://www.python.org/downloads/release/python-3110/
    echo    2. Download "Windows installer (64-bit)" 
    echo    3. IMPORTANT: Check "Add Python to PATH" during installation
    echo    4. Restart this setup after installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python 3.11.0 verified successfully
echo.r Bot - Setup
echo ===================================================
echo    YouTube Downloader Bot - Complete Setup v3.0
echo ===================================================
echo.
echo 🚀 This will install everything needed for the bot:
echo    • Python virtual environment
echo    • Required packages (telegram-bot, yt-dlp, etc.)
echo    • FFmpeg for video processing
echo    • Configuration files
echo    • Verification of installation
echo.
pause

:: Check if Python is installed
echo 📋 Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found!
    echo.
    echo 📥 Please install Python 3.8+ first:
    echo    1. Go to https://python.org/downloads/
    echo    2. Download Python 3.8 or higher
    echo    3. IMPORTANT: Check "Add Python to PATH" during installation
    echo    4. Restart this setup after Python installation
    echo.
    pause
    exit /b 1
)

echo ✅ Python found:
python --version
echo.

:: Check if FFmpeg is available
echo 📋 Checking FFmpeg installation...
ffmpeg\ffmpeg.exe -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  FFmpeg not found in package!
    echo.
    echo 📥 FFmpeg is required for video processing:
    echo    • The bot will try to use system FFmpeg
    echo    • For best compatibility, add ffmpeg folder to package
    echo    • Download from: https://ffmpeg.org/download.html
    echo.
    echo 🔄 Checking system FFmpeg...
    ffmpeg -version >nul 2>&1
    if %errorlevel% neq 0 (
        echo ❌ System FFmpeg not found either!
        echo.
        echo 💡 SOLUTIONS:
        echo    1. Download FFmpeg automatically [RECOMMENDED]
        echo    2. Download manually from https://ffmpeg.org/download.html
        echo    3. Install FFmpeg system-wide
        echo.
        set /p ffmpeg_choice="Download FFmpeg automatically? (Y/n): "
        if /i not "%ffmpeg_choice%"=="n" (
            call :download_ffmpeg
            if %errorlevel% equ 0 (
                echo ✅ FFmpeg downloaded successfully!
            ) else (
                echo ❌ FFmpeg download failed. Please download manually.
                echo 💡 Download from: https://www.gyan.dev/ffmpeg/builds/
                echo    Extract ffmpeg.exe to the 'ffmpeg' folder
            )
        ) else (
            echo ⚠️  The bot may not work properly without FFmpeg!
            set /p continue="Continue anyway? (y/N): "
            if /i not "%continue%"=="y" (
                echo Setup cancelled.
                pause
                exit /b 1
            )
        )
    ) else (
        echo ✅ System FFmpeg found and will be used
    )
) else (
    echo ✅ Package FFmpeg found:
    ffmpeg\ffmpeg.exe -version 2>&1 | findstr "ffmpeg version"
)
echo.

:: Create virtual environment
echo 🔧 Creating Python virtual environment...
if exist "venv\" (
    echo ⚠️  Virtual environment already exists, recreating...
    rmdir /s /q venv
)

python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment!
    echo Make sure Python is properly installed.
    pause
    exit /b 1
)

echo ✅ Virtual environment created
echo.

:: Activate virtual environment and install packages
echo 📦 Installing required packages...
call venv\Scripts\activate.bat

:: Upgrade pip first
python -m pip install --upgrade pip

:: Install required packages
pip install python-telegram-bot==13.15 yt-dlp python-dotenv

if %errorlevel% neq 0 (
    echo ❌ Failed to install packages!
    echo Check your internet connection and try again.
    pause
    exit /b 1
)

echo ✅ All packages installed successfully
echo.

:: Create .env file if it doesn't exist
echo ⚙️  Setting up configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo ✅ Configuration file created from template
    ) else (
        echo # Telegram Bot Configuration > .env
        echo TELEGRAM_BOT_TOKEN=your_bot_token_here >> .env
        echo. >> .env
        echo # Local Bot API Server >> .env
        echo LOCAL_API_SERVER=http://localhost:8081 >> .env
        echo. >> .env
        echo # Local API Server Credentials >> .env
        echo API_ID=your_api_id_here >> .env
        echo API_HASH=your_api_hash_here >> .env
        echo. >> .env
        echo # GPU Acceleration Settings
USE_GPU_ACCELERATION=true >> .env
        echo GPU_ENCODER=h264_nvenc >> .env
        echo. >> .env
        echo # FFmpeg Path (leave empty to use system FFmpeg) >> .env
        echo FFMPEG_PATH= >> .env
        echo. >> .env
        echo # Logging Level >> .env
        echo LOG_LEVEL=INFO >> .env
        echo ✅ Configuration file created
    )
) else (
    echo ✅ Configuration file already exists
)
echo.

:: Create downloads directory
if not exist "downloads\" (
    mkdir downloads
    echo ✅ Downloads directory created
)

:: Verify installation
echo 🔍 Verifying installation...
python -c "import telegram; import yt_dlp; import dotenv; print('✅ All packages verified')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Package verification failed!
    echo Some packages may not be installed correctly.
    pause
    exit /b 1
)

:: Final FFmpeg check and path setup
echo 🔍 Final FFmpeg verification...
if exist "ffmpeg\ffmpeg.exe" (
    echo ✅ Package FFmpeg ready
    echo FFMPEG_PATH=ffmpeg\ > .env.temp
    type .env >> .env.temp
    move .env.temp .env >nul
) else (
    ffmpeg -version >nul 2>&1
    if %errorlevel% equ 0 (
        echo ✅ System FFmpeg ready
    ) else (
        echo ⚠️  FFmpeg not available - video processing may fail
    )
)

echo.
echo ===================================================
echo                 SETUP COMPLETE! ✅
echo ===================================================
echo.
echo 🎯 NEXT STEPS:
echo.
echo 1. 📝 CONFIGURE BOT TOKEN:
echo    • Edit .env file
echo    • Replace 'your_bot_token_here' with your actual bot token
echo    • Get token from @BotFather on Telegram
echo.
echo 2. 🎬 (OPTIONAL) ENABLE 2GB SUPPORT:
echo    • Get API_ID and API_HASH from https://my.telegram.org/apps
echo    • Add them to .env file
echo.
echo 3. 🚀 START THE BOT:
echo    • run_with_local_api.bat (RECOMMENDED - Auto-start 2GB support)
echo    • run_without_local_api.bat (Standard 50MB limit)
echo.
echo 4. 🔍 VERIFY SETUP:
echo    • Run verify_package.bat anytime to check configuration
echo.
echo 📋 WHAT'S INCLUDED:
echo    ✅ Python virtual environment with all dependencies
echo    ✅ Configuration file (.env) ready for your tokens
echo    ✅ Local Bot API server for 2GB file support
echo    ✅ Enhanced launcher scripts with auto-start capability
echo    ✅ GPU acceleration support (NVIDIA)
echo    ✅ FFmpeg integration for video processing
echo    ✅ Smart file splitting for large videos
echo    ✅ Progress tracking and error handling
echo.
echo 💡 FFmpeg NOTICE:
if exist "ffmpeg\ffmpeg.exe" (
    echo    ✅ FFmpeg included in package
) else (
    echo    ⚠️  For optimal video processing, add FFmpeg to package
    echo    📥 Download: https://ffmpeg.org/download.html
    echo    📁 Extract to: ffmpeg\ folder in bot directory
)
echo.
echo 🎉 Your YouTube Downloader Bot v3.0 is ready!
echo    Just add your bot token and start downloading!
echo.
pause
goto :eof

:download_ffmpeg
echo.
echo 📥 Downloading FFmpeg...
echo    This may take a few minutes depending on your connection
echo.

:: Create ffmpeg directory if it doesn't exist
if not exist "ffmpeg" mkdir ffmpeg

:: Use PowerShell to download FFmpeg (Windows 10+ has PowerShell by default)
:: Download the latest release from gyan.dev (popular Windows FFmpeg builds)
set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "FFMPEG_ZIP=ffmpeg_temp.zip"
set "FFMPEG_TEMP=ffmpeg_temp"

echo 🌐 Downloading from: %FFMPEG_URL%
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%FFMPEG_ZIP%' -UserAgent 'Mozilla/5.0' } catch { Write-Host 'Download failed:' $_.Exception.Message; exit 1 } }"

if %errorlevel% neq 0 (
    echo ❌ Download failed! Please check your internet connection.
    exit /b 1
)

echo 📦 Extracting FFmpeg...
:: Extract using PowerShell (available on Windows 10+)
powershell -Command "& { try { Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('%FFMPEG_ZIP%', '%FFMPEG_TEMP%') } catch { Write-Host 'Extraction failed:' $_.Exception.Message; exit 1 } }"

if %errorlevel% neq 0 (
    echo ❌ Extraction failed!
    del "%FFMPEG_ZIP%" 2>nul
    exit /b 1
)

:: Find the bin directory and copy executables
echo 🔍 Locating FFmpeg executables...
for /r "%FFMPEG_TEMP%" %%i in (ffmpeg.exe) do (
    if exist "%%i" (
        echo 📋 Copying %%~nxi...
        copy "%%i" "ffmpeg\" >nul
        copy "%%~dpiffprobe.exe" "ffmpeg\" >nul 2>nul
        copy "%%~dpiffplay.exe" "ffmpeg\" >nul 2>nul
        goto :found_ffmpeg
    )
)

:found_ffmpeg
:: Clean up temporary files
echo 🧹 Cleaning up...
del "%FFMPEG_ZIP%" 2>nul
rmdir /s /q "%FFMPEG_TEMP%" 2>nul

:: Verify installation
if exist "ffmpeg\ffmpeg.exe" (
    echo ✅ FFmpeg installation complete!
    echo 📊 Version info:
    ffmpeg\ffmpeg.exe -version 2>&1 | findstr "ffmpeg version"
    exit /b 0
) else (
    echo ❌ FFmpeg installation failed!
    echo 💡 Please download manually from: https://www.gyan.dev/ffmpeg/builds/
    exit /b 1
)
