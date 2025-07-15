@echo off
echo ========================================
echo     YouTube Downloader Bot v3.0
echo     FFmpeg Automatic Downloader
echo ========================================
echo.

echo 📥 This script will download FFmpeg for video processing
echo 🎯 FFmpeg will be installed to: ffmpeg\ffmpeg.exe
echo 💾 Download size: ~100MB
echo.

set /p confirm="Continue with FFmpeg download? (Y/n): "
if /i "%confirm%"=="n" (
    echo Download cancelled.
    pause
    exit /b 0
)

echo.
echo 📥 Downloading FFmpeg...
echo    This may take a few minutes depending on your connection
echo.

:: Create ffmpeg directory if it doesn't exist
if not exist "ffmpeg" mkdir ffmpeg

:: Use PowerShell to download FFmpeg
set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
set "FFMPEG_ZIP=ffmpeg_temp.zip"
set "FFMPEG_TEMP=ffmpeg_temp"

echo 🌐 Downloading from: %FFMPEG_URL%
powershell -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; try { Write-Host 'Starting download...'; Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%FFMPEG_ZIP%' -UserAgent 'Mozilla/5.0' } catch { Write-Host 'Download failed:' $_.Exception.Message; exit 1 } }"

if %errorlevel% neq 0 (
    echo ❌ Download failed! Please check your internet connection.
    echo 💡 You can download manually from: https://www.gyan.dev/ffmpeg/builds/
    pause
    exit /b 1
)

echo 📦 Extracting FFmpeg...
powershell -Command "& { try { Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('%FFMPEG_ZIP%', '%FFMPEG_TEMP%') } catch { Write-Host 'Extraction failed:' $_.Exception.Message; exit 1 } }"

if %errorlevel% neq 0 (
    echo ❌ Extraction failed!
    del "%FFMPEG_ZIP%" 2>nul
    pause
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
    echo.
    echo ✅ FFmpeg installation complete!
    echo 📊 Version info:
    ffmpeg\ffmpeg.exe -version 2>&1 | findstr "ffmpeg version"
    echo.
    echo 🎯 FFmpeg is now ready for video processing!
    echo 📁 Location: %cd%\ffmpeg\ffmpeg.exe
) else (
    echo ❌ FFmpeg installation failed!
    echo 💡 Please download manually from: https://www.gyan.dev/ffmpeg/builds/
    echo 📁 Extract ffmpeg.exe to: %cd%\ffmpeg\
)

echo.
pause
