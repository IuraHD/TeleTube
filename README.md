# 🎬 TeleTube - YouTube Downloader Bot

[![Python 3.11.0](https://img.shields.io/badge/Python-3.11.0-blue.svg)](https://www.python.org/downloads/release/python-3110/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Telegram Bot API](https://img.shields.io/badge/Telegram%20Bot%20API-13.15-blue.svg)](https://core.telegram.org/bots/api)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red.svg)](https://github.com/yt-dlp/yt-dlp)
[![GitHub release](https://img.shields.io/github/release/IuraHD/TeleTube.svg)](https://github.com/IuraHD/TeleTube/releases)
[![GitHub issues](https://img.shields.io/github/issues/IuraHD/TeleTube.svg)](https://github.com/IuraHD/TeleTube/issues)

A powerful Telegram bot for downloading YouTube videos with GPU acceleration, auto-starting local API support, and intelligent file splitting.

## 🚀 New Features

- **🔄 Auto-Start Local API**: Automatically starts and manages local API server
- **📱 Smart Upload Logic**: Split files upload as videos when possible (not documents)
- **🎯 Clean ASCII Interface**: Beautiful console output without garbled Unicode
- **⚡ Enhanced GPU Acceleration**: Optimized NVIDIA NVENC encoding
- **🛡️ Robust Error Handling**: Comprehensive validation and fallback systems

## 📦 Core Features

- **🎬 High Quality Downloads**: Support for up to 4K resolution
- **⚡ GPU Acceleration**: NVIDIA NVENC hardware encoding for faster processing
- **📱 Mobile Optimized**: Videos optimized for Telegram's player on all devices
- **🗂️ Smart File Splitting**: Automatic splitting for large files with video streaming support
- **🏠 Local API Support**: 2GB file uploads vs 50MB standard limit with auto-start
- **🔄 Auto-Fallback**: Seamlessly switches between local and standard API
- **📊 Progress Tracking**: Real-time download and upload progress
- **🎯 Quality Selection**: Multiple quality options with size estimates

## 🚀 Quick Start

### Option 1: Clone from GitHub (Recommended)
```bash
git clone https://github.com/yourusername/TeleTube.git
cd TeleTube
```

### Option 2: Download Release
Download the latest release from the [Releases page](https://github.com/yourusername/TeleTube/releases).

### 1. **Setup**
```batch
setup.bat          # Windows
./setup.sh          # Linux/Mac
```
This will:
- Install Python dependencies
- Create virtual environment  
- Set up configuration files
- **Auto-download FFmpeg** (if not found)
- Verify installation

### 3. **Configure Bot Token**
Edit `.env` file and add your Telegram bot token:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram.

### 4. **Start the Bot**
Choose your preferred mode:

**🏠 Local API Mode (2GB limit) - RECOMMENDED:**
```batch
run_with_local_api.bat
```
- Automatically starts local API server
- Enables 2GB file uploads
- Falls back to standard API if setup fails

**☁️ Standard Mode (50MB limit):**
```batch
run_without_local_api.bat
```
- Uses standard Telegram API
- No additional setup required
- 50MB file size limit

## ⚙️ Configuration Options

### Required Settings (.env file):
- `TELEGRAM_BOT_TOKEN` - Your bot token from @BotFather

### Optional Settings for 2GB Support:
- `API_ID` - From https://my.telegram.org/apps (auto-configured by launcher)
- `API_HASH` - From https://my.telegram.org/apps (auto-configured by launcher)

### Advanced Settings:
- `USE_GPU_ACCELERATION=true` - Enable NVIDIA GPU encoding
- `GPU_ENCODER=h264_nvenc` - GPU encoder type (h264_nvenc, h264_amf, h264_qsv)
- `LOG_LEVEL=INFO` - Logging level

## 🎯 File Size Limits & Smart Splitting

| Mode | File Limit | Split Threshold | Split Part Size | Upload Type |
|------|------------|-----------------|-----------------|-------------|
| **Standard API** | 50MB | 45MB | 40MB | Video (when possible) |
| **Local API** | 2GB | 1.8GB | 1GB | Video (when possible) |

### Smart Upload Logic:
- **Small parts (under limit)**: Upload as video with streaming support
- **Large parts (over limit)**: Upload as document for reliability
- **Multiple parts**: Numbered sequentially (Part 1, Part 2, etc.)

## 📱 Launcher Comparison

| Launcher | Description | Auto-Start API | Fallback | Best For |
|----------|-------------|----------------|----------|----------|
| `run_with_local_api.bat` | **RECOMMENDED** | ✅ Yes | ✅ To Standard | Most users |
| `run_without_local_api.bat` | Standard only | ❌ No | ❌ None | Quick testing |

## 📋 System Requirements

- **OS**: Windows 10/11
- **Python**: 3.8 or higher (automatically checked)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space for downloads
- **GPU**: NVIDIA GPU (optional, for hardware acceleration)
- **Network**: Stable internet connection

## 📁 Package Contents

```
YouTube-Bot-Package/
├── yt_downloader_bot.py          # Main bot script with enhanced features
├── setup.bat                     # Complete setup installer
├── setup.sh                      # Linux/Mac setup (cross-platform)
├── verify_package.bat            # Installation verification
├── .env.example                  # Configuration template
├── requirements.txt              # Python dependencies
├── README.md                     # This file
├── SETUP_GUIDE.md               # Detailed setup guide
├── PACKAGE_CONTENTS.md          # File listing and descriptions
├── run_without_local_api.bat    # Standard API launcher (50MB)
├── run_with_local_api.bat       # Auto-start Local API launcher (2GB)
├── run_without_local_api.sh     # Linux/Mac standard launcher
├── run_with_local_api.sh        # Linux/Mac local API launcher  
└── api_server/                   # Local Bot API server files
    ├── telegram-bot-api.exe      # Windows executable
    ├── libcrypto-3-x64.dll      # Required libraries
    ├── libssl-3-x64.dll         # SSL support
    ├── zlib1.dll                # Compression library
    └── ...                       # Additional support files
```

## 🔧 Troubleshooting

**Bot not responding?**
- Check bot token in `.env` file
- Verify internet connection
- Run `verify_package.bat` to check setup

**"Python not found" error?**
- Install Python from https://python.org/downloads/
- Make sure to check "Add Python to PATH"

**Local API server won't start?**
- Check API_ID and API_HASH in `.env` file
- Get credentials from https://my.telegram.org/apps
- Bot will automatically fall back to standard API

**Large files not uploading?**
- Use `run_with_local_api.bat` for 2GB support
- Files >2GB will be automatically split
- Split parts upload as videos when possible

**GPU acceleration not working?**
- Requires NVIDIA GPU with recent drivers
- Set `USE_GPU_ACCELERATION=false` to disable
- Bot works fine with CPU-only processing

**Unicode/emoji display issues?**
- Console output uses clean ASCII characters
- No impact on bot functionality
- Telegram messages display properly regardless

## 🎯 Usage Tips

**For Best Performance:**
1. Use `run_with_local_api.bat` (recommended)
2. Enable GPU acceleration if you have NVIDIA GPU
3. Ensure stable internet connection
4. Close other intensive applications during large downloads

**File Organization:**
- Downloads folder is automatically cleaned after upload
- Bot logs are saved to `bot.log` and `user_activity.log`
- Configuration changes in `.env` take effect on next restart

## 🆘 Support

If you encounter issues:

1. Run `verify_package.bat` to check installation
2. Check the `bot.log` file for error details
3. Ensure all required fields in `.env` are configured
4. Try `run_without_local_api.bat` for basic functionality testing

## 📄 License

This software is provided as-is for educational and personal use.

## 🚀 Version

**Version**: 3.0  
**Build Date**: July 2025  
**Compatibility**: Windows 10/11, **Python 3.11.0 required**

### Version 3.0 Highlights:
- **Auto-Start Local API**: One-click 2GB support
- **Smart Upload Logic**: Split files as videos when possible  
- **Clean ASCII Interface**: Professional console output
- **Enhanced Error Handling**: Robust fallback systems
- **Cross-Platform Support**: Linux/Mac launchers included
