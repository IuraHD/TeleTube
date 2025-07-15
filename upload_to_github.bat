@echo off
REM TeleTube - Quick Upload to GitHub Script
REM Repository: https://github.com/IuraHD/TeleTube

echo.
echo ====================================
echo   TeleTube - GitHub Upload Script
echo ====================================
echo.

echo [1/5] Staging all files...
git add .
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to stage files!
    pause
    exit /b 1
)

echo [2/5] Creating initial commit...
git commit -m "🎉 Initial release: TeleTube v3.0 - YouTube Downloader Bot

✨ Features:
- 🎬 YouTube video downloading with quality selection
- ⚡ GPU acceleration (NVIDIA NVENC) support
- 🏠 Local API support for 2GB+ file uploads
- 📱 Smart file splitting and mobile optimization
- 🔧 Portable Python distribution option
- 🌐 Cross-platform support (Windows/Linux/Mac)
- 📊 Real-time download progress tracking
- 🛡️ Comprehensive error handling and logging
- 🔒 Security-first design with .env protection

🔧 Technical Stack:
- Python 3.11.0 (enforced requirement)
- Telegram Bot API 13.15
- yt-dlp for YouTube downloading
- FFmpeg with GPU acceleration
- GitHub Actions CI/CD pipeline

📚 Documentation:
- Complete setup guides for all platforms
- Contributing guidelines for developers
- Security policy for vulnerability reporting
- Issue/PR templates for GitHub integration

🎯 Ready for production use with comprehensive documentation!"

if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to create commit!
    pause
    exit /b 1
)

echo [3/5] Setting main branch...
git branch -M main
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to set main branch!
    pause
    exit /b 1
)

echo [4/5] Adding GitHub remote...
git remote add origin https://github.com/IuraHD/TeleTube.git
if %ERRORLEVEL% neq 0 (
    echo WARNING: Remote might already exist, continuing...
)

echo [5/5] Pushing to GitHub...
echo.
echo ⚠️  You may need to authenticate with GitHub!
echo    Use your GitHub username and personal access token
echo.
git push -u origin main

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Upload failed! This might be because:
    echo    1. Repository doesn't exist on GitHub yet
    echo    2. Authentication failed
    echo    3. Network issues
    echo.
    echo 📋 Next steps:
    echo    1. Create repository 'TeleTube' on GitHub (https://github.com/new)
    echo    2. Run this script again
    echo    3. Or follow manual steps in UPLOAD_COMMANDS.md
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ SUCCESS! TeleTube uploaded to GitHub!
echo.
echo 🎯 Next steps:
echo    1. Visit: https://github.com/IuraHD/TeleTube
echo    2. Set repository description: "🎬 Powerful Telegram bot for downloading YouTube videos with GPU acceleration and 2GB file support"
echo    3. Add topics: telegram-bot, youtube-downloader, python, ffmpeg, gpu-acceleration, yt-dlp
echo    4. Enable Issues and Discussions
echo    5. Create your first release (v3.0.0)
echo.
echo 🎉 Congratulations! Your project is now live on GitHub!
echo.
pause
