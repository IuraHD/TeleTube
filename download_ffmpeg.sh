#!/bin/bash

echo "========================================"
echo "   YouTube Downloader Bot v3.0"
echo "   FFmpeg Automatic Downloader"
echo "========================================"
echo

echo "📥 This script will download FFmpeg for video processing"
echo "🎯 FFmpeg will be installed to: ffmpeg/ffmpeg"
echo "💾 Download size: ~50-100MB depending on platform"
echo

read -p "Continue with FFmpeg download? (Y/n): " confirm
if [[ "$confirm" =~ ^[Nn]$ ]]; then
    echo "Download cancelled."
    exit 0
fi

# FFmpeg download function
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
            exit 1
        fi
    else
        echo "❌ Unsupported OS: $OS"
        exit 1
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
        exit 1
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ Download failed! Please check your internet connection."
        exit 1
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
            exit 1
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
        echo
        echo "✅ FFmpeg installation complete!"
        echo "📊 Version info:"
        ./ffmpeg/ffmpeg -version 2>&1 | head -1
        echo
        echo "🎯 FFmpeg is now ready for video processing!"
        echo "📁 Location: $(pwd)/ffmpeg/ffmpeg"
        return 0
    else
        echo "❌ FFmpeg installation failed!"
        echo "💡 Please install manually using your package manager"
        exit 1
    fi
}

# Run the download
download_ffmpeg

echo
