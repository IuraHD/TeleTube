@echo off
echo YouTube Downloader Bot v3.0 - Final Build Verification
echo.

echo Checking package structure...
set ERROR_COUNT=0

REM Check core files
if not exist "yt_downloader_bot.py" (
    echo ERROR: Main bot file missing
    set /a ERROR_COUNT+=1
)

if not exist "requirements.txt" (
    echo ERROR: Requirements file missing
    set /a ERROR_COUNT+=1
)

if not exist ".env.example" (
    echo ERROR: Environment template missing
    set /a ERROR_COUNT+=1
)

REM Check documentation
if not exist "README.md" (
    echo ERROR: README missing
    set /a ERROR_COUNT+=1
)

if not exist "SETUP_GUIDE.md" (
    echo ERROR: Setup guide missing
    set /a ERROR_COUNT+=1
)

if not exist "PACKAGE_CONTENTS.md" (
    echo ERROR: Package contents missing
    set /a ERROR_COUNT+=1
)

REM Check scripts
if not exist "setup.bat" (
    echo ERROR: Windows setup script missing
    set /a ERROR_COUNT+=1
)

if not exist "setup.sh" (
    echo ERROR: Unix setup script missing
    set /a ERROR_COUNT+=1
)

if not exist "run_with_local_api.bat" (
    echo ERROR: Local API launcher Windows missing
    set /a ERROR_COUNT+=1
)

if not exist "run_with_local_api.sh" (
    echo ERROR: Local API launcher Unix missing
    set /a ERROR_COUNT+=1
)

if not exist "run_without_local_api.bat" (
    echo ERROR: Standard launcher Windows missing
    set /a ERROR_COUNT+=1
)

if not exist "run_without_local_api.sh" (
    echo ERROR: Standard launcher Unix missing
    set /a ERROR_COUNT+=1
)

if not exist "start_local_api.sh" (
    echo ERROR: API server launcher Unix missing
    set /a ERROR_COUNT+=1
)

REM Check API server
if not exist "api_server\" (
    echo ERROR: API server folder missing
    set /a ERROR_COUNT+=1
) else (
    if not exist "api_server\telegram-bot-api.exe" (
        echo ERROR: Telegram Bot API executable missing
        set /a ERROR_COUNT+=1
    )
)

REM Check FFmpeg folder
if not exist "ffmpeg\" (
    echo ERROR: FFmpeg folder missing
    set /a ERROR_COUNT+=1
)

REM Check downloads folder
if not exist "downloads\" (
    echo Creating downloads folder...
    mkdir downloads
)

echo.
echo Package verification complete
echo Error count: %ERROR_COUNT%

if %ERROR_COUNT% equ 0 (
    echo SUCCESS: Package structure is COMPLETE
    echo SUCCESS: Ready for distribution
    echo.
    echo Package features:
    echo - Cross-platform support Windows/Linux/Mac
    echo - Local Bot API server for 2GB file support
    echo - FFmpeg integration for video processing
    echo - GPU acceleration support
    echo - Clean ASCII interface
    echo - Comprehensive documentation
    echo - Auto-start functionality
    echo - Smart file handling
    echo.
    echo YouTube Downloader Bot v3.0 - READY FOR DEPLOYMENT
) else (
    echo FAILED: Package has %ERROR_COUNT% missing components
    echo Please fix these issues before distribution
)

echo.
pause
