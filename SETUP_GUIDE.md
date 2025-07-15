# 🛠️ YouTube Downloader Bot - Setup Guide

Complete step-by-step installation guide for any Windows PC with auto-starting local API support.

## 📋 Prerequisites

Before you begin, ensure you have:
- Windows 10 or Windows 11
- Administrator privileges (for Python installation)
- **Python 3.11.0** (specific version required)
- Stable internet connection
- At least 2GB free disk space

## 🚀 Installation Steps

### Step 1: Download Python 3.11.0

**⚠️ IMPORTANT: This bot requires Python 3.11.0 specifically**

1. Visit https://www.python.org/downloads/release/python-3110/
2. Download **"Windows installer (64-bit)"**
3. **CRITICAL**: During installation, check "Add Python to PATH"
4. Complete the installation
5. Restart your computer after installation

**Verify installation:**
```cmd
python --version
```
Should show: `Python 3.11.0`

### Step 2: Get Your Bot Token

1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token (it looks like: `123456789:ABCdefGHIjklMNOpqrSTUvwxyz`)
5. Keep this token safe - you'll need it in Step 4

### Step 3: Run Automatic Setup

1. Extract the bot package to any folder (e.g., `C:\YouTube-Bot\`)
2. Double-click `setup.bat`
3. Wait for the installation to complete
4. The setup will:
   - Create a Python virtual environment
   - Install all required packages
   - Create configuration files
   - Verify the installation

### Step 4: Configure Your Bot

1. Open the `.env` file in a text editor (Notepad works fine)
2. Replace `your_bot_token_here` with your actual bot token:
   ```
   TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxyz
   ```
3. Save the file

### Step 5: (Optional) Enable 2GB File Support with Auto-Start

**🏠 NEW: Auto-Start Local API (RECOMMENDED)**

The `run_with_local_api.bat` launcher now automatically:
- Starts the local API server if needed
- Validates your API credentials
- Falls back to standard API if there are issues
- Provides 2GB file upload support

For this to work:

1. Visit https://my.telegram.org/apps
2. Log in with your Telegram account
3. Create a new application
4. Copy your `API_ID` and `API_HASH`
5. Add them to the `.env` file:
   ```
   API_ID=12345678
   API_HASH=abcdef1234567890abcdef1234567890
   ```

### Step 6: Start Your Bot

**🚀 RECOMMENDED - Auto-Start Local API (2GB files):**
```batch
run_with_local_api.bat
```
- Automatically starts local API server
- Enables 2GB file uploads
- Falls back to 50MB if setup fails
- One-click solution!

**🔰 Standard API Only (50MB files):**
```batch
run_without_local_api.bat
```
- Uses standard Telegram API
- No additional setup required
- 50MB file size limit

## 🎯 Verification

Run `verify_package.bat` anytime to check if everything is properly installed and configured.

## � Console Output

The bot now uses clean ASCII characters for console output:
- `[*]` - Starting/Processing actions
- `[+]` - Success/Positive actions  
- `[!]` - Errors/Warnings
- `[i]` - Information/Tips
- `[~]` - Waiting/Progress states

Example output:
```
[*] Starting YouTube Bot with Local API Server...
[+] Starting Local Bot API Server...
[i] Loading API credentials from .env file...
[+] API credentials loaded
[*] Starting Local Bot API Server on port 8081...
[~] Waiting for server to initialize...
[+] Local API detected, configuring for local server...

===============================================================================
                              STARTING YOUTUBE BOT
===============================================================================

[+] Configuration set for local API (2GB file limit)
[*] Starting bot with Local API...
```

## �🔧 Configuration Options

### Basic Settings (.env file)
```bash
# Required: Your bot token from @BotFather
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional: For 2GB file support (from my.telegram.org/apps)
API_ID=your_api_id_here
API_HASH=your_api_hash_here

# Performance Settings
USE_GPU_ACCELERATION=true    # Enable if you have NVIDIA GPU
GPU_ENCODER=h264_nvenc      # GPU encoder type
LOG_LEVEL=INFO              # Logging detail level
```

### File Size Limits
| Setting | Upload Limit | When to Use |
|---------|-------------|-------------|
| Standard API | 50MB | Quick setup, most videos |
| Local API | 2GB | Long videos, high quality |

## 📱 How to Use

1. Start your bot using one of the launch scripts
2. Open Telegram and find your bot
3. Send `/start` to begin
4. Send any YouTube link
5. Choose video quality
6. Download and enjoy!

## 🆘 Troubleshooting

### Common Issues

**"Python is not recognized"**
- Reinstall Python and check "Add Python to PATH"
- Restart your computer after installation

**"Bot token is invalid"**
- Double-check the token in `.env` file
- Make sure there are no extra spaces
- Get a new token from @BotFather if needed

**"Permission denied" errors**
- Run setup.bat as Administrator
- Check antivirus software isn't blocking the installation

**Large files won't upload**
- Make sure you've configured API_ID and API_HASH
- Use `run_with_local_api.bat` for 2GB support
- Check that local API server is running

**GPU acceleration not working**
- Requires NVIDIA GPU with recent drivers
- Set `USE_GPU_ACCELERATION=false` to disable

### Log Files

Check these files for detailed error information:
- `bot.log` - General bot operations
- `user_activity.log` - User download history

## 🔄 Updates

To update the bot:
1. Replace `yt_downloader_bot.py` with new version
2. Run `setup.bat` again if dependencies changed
3. Restart the bot

## 📞 Support

If you still have issues:
1. Run `verify_package.bat` and check for errors
2. Look at the error messages in `bot.log`
3. Make sure all configuration values in `.env` are correct
4. Try the standard API mode first before local API

## 🎉 Success!

Once everything is working, you'll see:
```
🚀 Bot is ready! Send YouTube links to start downloading.
```

Your bot is now ready to download YouTube videos for you and your users!
