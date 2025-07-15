#!/bin/bash
# YouTube Downloader Bot - Setup Script for Linux/Mac v3.0
# This script sets up the bot environment on Unix-based systems

echo "=================================================="
echo "   YouTube Downloader Bot - Complete Setup v3.0"
echo "=================================================="
echo
echo "🚀 This will install everything needed for the bot:"
echo "   • Python virtual environment"
echo "   • Required packages (telegram-bot, yt-dlp, etc.)"
echo "   • FFmpeg for video processing"
echo "   • Configuration files"
echo "   • Verification of installation"
echo
read -p "Press Enter to continue..."

# Check if Python is installed
echo "📋 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found!"
    echo
    echo "📥 Please install Python 3.11.0 first:"
    echo "   Ubuntu/Debian: sudo apt update && sudo apt install python3.11 python3.11-pip python3.11-venv"
    echo "   macOS: brew install python@3.11"
    echo "   Or download from: https://www.python.org/downloads/release/python-3110/"
    echo
    exit 1
fi

# Check Python version - require 3.11.0
echo "📋 Verifying Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ Python found: $PYTHON_VERSION"

# Extract major.minor version
PYTHON_MAJOR_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f1,2)

if [ "$PYTHON_MAJOR_MINOR" != "3.11" ]; then
    echo "⚠️  Python version mismatch!"
    echo
    echo "❌ Required: Python 3.11.0"
    echo "❌ Found:    Python $PYTHON_VERSION"
    echo
    echo "📥 Please install Python 3.11.0:"
    echo "   Ubuntu/Debian: sudo apt update && sudo apt install python3.11 python3.11-pip python3.11-venv"
    echo "   CentOS/RHEL:   sudo dnf install python3.11 python3.11-pip"
    echo "   macOS:         brew install python@3.11"
    echo "   Or download from: https://www.python.org/downloads/release/python-3110/"
    echo
    exit 1
fi

echo "✅ Python 3.11.0 verified successfully"
echo

# Check if FFmpeg is available
echo "📋 Checking FFmpeg installation..."
if [ -f "ffmpeg/ffmpeg" ]; then
    echo "✅ Package FFmpeg found:"
    ./ffmpeg/ffmpeg -version 2>&1 | head -1
elif command -v ffmpeg &> /dev/null; then
    echo "✅ System FFmpeg found:"
    ffmpeg -version 2>&1 | head -1
else
    echo "⚠️  FFmpeg not found!"
    echo
    echo "📥 FFmpeg is required for video processing:"
    echo "   1. Install via package manager [RECOMMENDED]:"
    echo "      Ubuntu/Debian: sudo apt install ffmpeg"
    echo "      CentOS/RHEL:   sudo yum install ffmpeg"
    echo "      macOS:         brew install ffmpeg"
    echo "   2. Download static binary automatically"
    echo "   3. Add static FFmpeg binary to ffmpeg/ folder manually"
    echo
    read -p "Download FFmpeg static binary automatically? (Y/n): " ffmpeg_choice
    if [[ ! "$ffmpeg_choice" =~ ^[Nn]$ ]]; then
        download_ffmpeg
        if [ $? -eq 0 ]; then
            echo "✅ FFmpeg downloaded successfully!"
        else
            echo "❌ FFmpeg download failed. Please install manually."
        fi
    else
        echo "⚠️  The bot may not work properly without FFmpeg!"
        read -p "Continue anyway? (y/N): " continue_choice
        if [[ ! "$continue_choice" =~ ^[Yy]$ ]]; then
            echo "Setup cancelled."
            exit 1
        fi
    fi
    echo "⚠️  The bot may not work properly without FFmpeg!"
    echo
    read -p "Continue anyway? (y/N): " continue
    if [[ ! "$continue" =~ ^[Yy]$ ]]; then
        echo "Setup cancelled."
        exit 1
    fi
fi
echo

# Create virtual environment
echo "🔧 Creating Python virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists, recreating..."
    rm -rf venv
fi

python3 -m venv venv
if [ $? -ne 0 ]; then
    echo "❌ Failed to create virtual environment!"
    echo "Make sure Python3 and python3-venv are properly installed."
    exit 1
fi

echo "✅ Virtual environment created"
echo

# Activate virtual environment and install packages
echo "📦 Installing required packages..."
source venv/bin/activate

# Upgrade pip first
python -m pip install --upgrade pip

# Install required packages
pip install python-telegram-bot==13.15 yt-dlp python-dotenv

if [ $? -ne 0 ]; then
    echo "❌ Failed to install packages!"
    echo "Check your internet connection and try again."
    exit 1
fi

echo "✅ All packages installed successfully"
echo

# Create .env file if it doesn't exist
echo "⚙️  Setting up configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp ".env.example" ".env"
        echo "✅ Configuration file created from template"
    else
        cat > .env << 'EOF'
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Local Bot API Server
LOCAL_API_SERVER=http://localhost:8081

# Local API Server Credentials
API_ID=your_api_id_here
API_HASH=your_api_hash_here

# GPU Acceleration Settings
USE_GPU_ACCELERATION=true
GPU_ENCODER=h264_nvenc

# Logging Level
LOG_LEVEL=INFO
EOF
        echo "✅ Configuration file created"
    fi
else
    echo "✅ Configuration file already exists"
fi
echo

# Create downloads directory
if [ ! -d "downloads" ]; then
    mkdir downloads
    echo "✅ Downloads directory created"
fi

# Verify installation
echo "🔍 Verifying installation..."
python -c "import telegram; import yt_dlp; import dotenv; print('✅ All packages verified')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Package verification failed!"
    echo "Some packages may not be installed correctly."
    exit 1
fi

echo
echo "=================================================="
echo "                SETUP COMPLETE! ✅"
echo "=================================================="
echo
echo "🎯 NEXT STEPS:"
echo
echo "1. 📝 CONFIGURE BOT TOKEN:"
echo "   • Edit .env file: nano .env"
echo "   • Replace 'your_bot_token_here' with your actual bot token"
echo "   • Get token from @BotFather on Telegram"
echo
echo "2. 🎬 (OPTIONAL) ENABLE 2GB SUPPORT:"
echo "   • Get API_ID and API_HASH from https://my.telegram.org/apps"
echo "   • Add them to .env file"
echo
echo "3. 🚀 START THE BOT:"
echo "   • Standard mode: ./run_without_local_api.sh"
echo "   • Local API mode: ./run_with_local_api.sh"
echo "   • Auto-fallback: ./start_with_local_api.sh"
echo
echo "4. 🔍 VERIFY SETUP:"
echo "   • Run ./verify_package.sh anytime to check configuration"
echo
echo "📋 WHAT'S INCLUDED:"
echo "   ✅ Python virtual environment with all dependencies"
echo "   ✅ Configuration file (.env) ready for your tokens"
echo "   ✅ Multiple launcher scripts for different modes"
echo "   ✅ GPU acceleration support"
echo "   ✅ Smart file splitting for large videos"
echo "   ✅ Progress tracking and error handling"
echo
echo "🎉 Your YouTube Downloader Bot is ready!"
echo "   Just add your bot token and start downloading!"
echo

# FFmpeg download function for Linux/Mac
download_ffmpeg() {
    echo
    echo "📥 Downloading FFmpeg static binary..."
    echo "   This may take a few minutes depending on your connection"
    echo
    
    # Create ffmpeg directory if it doesn't exist
    mkdir -p ffmpeg
    
    # Detect architecture and OS for appropriate download
    ARCH=$(uname -m)
    OS=$(uname -s)
    
    if [[ "$OS" == "Darwin" ]]; then
        # macOS
        echo "🍎 Detected macOS"
        FFMPEG_URL="https://evermeet.cx/ffmpeg/ffmpeg-6.0.zip"
        FFMPEG_ZIP="ffmpeg_temp.zip"
    elif [[ "$OS" == "Linux" ]]; then
        # Linux
        if [[ "$ARCH" == "x86_64" ]]; then
            echo "🐧 Detected Linux x64"
            FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz"
            FFMPEG_ARCHIVE="ffmpeg_temp.tar.xz"
        elif [[ "$ARCH" == "aarch64" ]] || [[ "$ARCH" == "arm64" ]]; then
            echo "🐧 Detected Linux ARM64"
            FFMPEG_URL="https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz"
            FFMPEG_ARCHIVE="ffmpeg_temp.tar.xz"
        else
            echo "❌ Unsupported architecture: $ARCH"
            echo "💡 Please install FFmpeg manually:"
            echo "   Ubuntu/Debian: sudo apt install ffmpeg"
            echo "   CentOS/RHEL:   sudo yum install ffmpeg"
            return 1
        fi
    else
        echo "❌ Unsupported OS: $OS"
        return 1
    fi
    
    echo "🌐 Downloading from appropriate source..."
    
    # Download with curl or wget
    if command -v curl &> /dev/null; then
        if [[ "$OS" == "Darwin" ]]; then
            curl -L -o "$FFMPEG_ZIP" "$FFMPEG_URL"
        else
            curl -L -o "$FFMPEG_ARCHIVE" "$FFMPEG_URL"
        fi
    elif command -v wget &> /dev/null; then
        if [[ "$OS" == "Darwin" ]]; then
            wget -O "$FFMPEG_ZIP" "$FFMPEG_URL"
        else
            wget -O "$FFMPEG_ARCHIVE" "$FFMPEG_URL"
        fi
    else
        echo "❌ Neither curl nor wget found. Please install one of them."
        return 1
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ Download failed! Please check your internet connection."
        return 1
    fi
    
    echo "📦 Extracting FFmpeg..."
    
    if [[ "$OS" == "Darwin" ]]; then
        # macOS - extract ZIP
        if command -v unzip &> /dev/null; then
            unzip -q "$FFMPEG_ZIP" -d ffmpeg/
            rm "$FFMPEG_ZIP"
        else
            echo "❌ unzip not found. Please install unzip or download manually."
            rm "$FFMPEG_ZIP"
            return 1
        fi
    else
        # Linux - extract tar.xz
        TEMP_DIR="ffmpeg_temp"
        mkdir -p "$TEMP_DIR"
        tar -xf "$FFMPEG_ARCHIVE" -C "$TEMP_DIR" --strip-components=1
        
        # Copy binaries to ffmpeg folder
        if [ -f "$TEMP_DIR/ffmpeg" ]; then
            cp "$TEMP_DIR/ffmpeg" ffmpeg/
            chmod +x ffmpeg/ffmpeg
        fi
        if [ -f "$TEMP_DIR/ffprobe" ]; then
            cp "$TEMP_DIR/ffprobe" ffmpeg/
            chmod +x ffmpeg/ffprobe
        fi
        
        # Clean up
        rm -rf "$TEMP_DIR" "$FFMPEG_ARCHIVE"
    fi
    
    # Verify installation
    if [ -f "ffmpeg/ffmpeg" ]; then
        echo "✅ FFmpeg installation complete!"
        echo "📊 Version info:"
        ./ffmpeg/ffmpeg -version 2>&1 | head -1
        return 0
    else
        echo "❌ FFmpeg installation failed!"
        echo "💡 Please install manually using your package manager"
        return 1
    fi
}
