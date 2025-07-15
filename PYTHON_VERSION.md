# Python 3.11.0 Requirement

## ⚠️ Important Version Requirement

This YouTube Downloader Bot **requires Python 3.11.0 specifically**.

## Why Python 3.11.0?

- **Performance**: Python 3.11.0 offers significant performance improvements (10-60% faster)
- **Memory efficiency**: Better memory usage for video processing
- **Compatibility**: All dependencies are fully tested with Python 3.11.0
- **Stability**: Proven stable version for production use

## Installation Instructions

### Windows
1. Visit: https://www.python.org/downloads/release/python-3110/
2. Download: **"Windows installer (64-bit)"**
3. ⚠️ **CRITICAL**: Check "Add Python to PATH" during installation
4. Complete installation and restart your computer

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3.11 python3.11-pip python3.11-venv
```

### Linux (CentOS/RHEL)
```bash
sudo dnf install python3.11 python3.11-pip
```

### macOS
```bash
brew install python@3.11
```

## Verification

After installation, verify the version:
```bash
python --version
```
Should output: `Python 3.11.0`

## Setup Scripts

The setup scripts (`setup.bat` and `setup.sh`) will automatically check for Python 3.11.0 and guide you through installation if needed.

## Troubleshooting

**Q: I have Python 3.12+ installed, will it work?**
A: No, the bot is specifically designed for Python 3.11.0. Newer versions may have compatibility issues.

**Q: Can I use Python 3.10 or older?**
A: No, the bot requires features and performance improvements only available in Python 3.11.0.

**Q: I get "Python not found" error**
A: Make sure you checked "Add Python to PATH" during installation and restart your terminal/computer.
