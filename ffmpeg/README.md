# FFmpeg Integration

This folder should contain FFmpeg binaries for video processing.

## Windows Structure:
```
ffmpeg/
├── ffmpeg.exe          # Main FFmpeg executable
├── ffprobe.exe         # Media analysis tool
└── ffplay.exe          # Media player (optional)
```

## Linux/Mac Structure:
```
ffmpeg/
├── ffmpeg              # Main FFmpeg executable
├── ffprobe             # Media analysis tool
└── ffplay              # Media player (optional)
```

## Download FFmpeg:

### Windows:
1. Download from: https://www.gyan.dev/ffmpeg/builds/
2. Extract the archive
3. Copy `ffmpeg.exe`, `ffprobe.exe` from `bin/` folder to this directory

### Linux:
1. Install via package manager: `sudo apt install ffmpeg` (Ubuntu/Debian)
2. Or download static build from: https://johnvansickle.com/ffmpeg/
3. Extract and copy binaries to this folder

### macOS:
1. Install via Homebrew: `brew install ffmpeg`
2. Or download from: https://evermeet.cx/ffmpeg/
3. Copy binaries to this folder

## Configuration:

The bot will automatically detect FFmpeg in this order:
1. Package FFmpeg (this folder)
2. System FFmpeg (PATH)
3. Custom path (FFMPEG_PATH in .env)

## Why FFmpeg is needed:

- Video format conversion
- Quality optimization for Telegram
- Hardware acceleration (GPU encoding)
- Audio/video merging for split downloads
- Metadata handling
- Streaming optimization

## File Size:
- Complete FFmpeg package: ~100-150MB
- Essential for professional video processing
- Required for GPU acceleration features
