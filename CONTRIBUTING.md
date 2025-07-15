# Contributing to TeleTube

Thank you for your interest in contributing to TeleTube! This document provides guidelines for contributing to the project.

## 🚀 Getting Started

### Prerequisites
- **Python 3.11.0** (required)
- Git
- A Telegram bot token for testing

### Setting up Development Environment

1. **Fork and Clone**
   ```bash
   git clone https://github.com/yourusername/TeleTube.git
   cd TeleTube
   ```

2. **Run Setup**
   ```bash
   # Windows
   setup.bat
   
   # Linux/Mac  
   ./setup.sh
   ```

3. **Configure for Testing**
   ```bash
   cp .env.example .env
   # Edit .env with your test bot token
   ```

## 📋 Development Guidelines

### Code Style
- Follow PEP 8 Python style guide
- Use descriptive variable and function names
- Add comments for complex logic
- Keep functions focused and small

### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove)
- Reference issues when applicable

Examples:
```
Add GPU acceleration support for AMD cards
Fix file splitting for large videos
Update README with new installation steps
```

### Testing
- Test your changes with different video types
- Verify both local and standard API modes work
- Test on both small and large files
- Ensure error handling works properly

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Details**
   - Operating System
   - Python version
   - Bot version/commit hash

2. **Steps to Reproduce**
   - Clear step-by-step instructions
   - Expected vs actual behavior

3. **Logs**
   - Relevant portions of `bot.log`
   - Console output (remove sensitive tokens)

4. **Additional Context**
   - Video URL that caused the issue (if applicable)
   - Screenshots if relevant

## 💡 Feature Requests

For feature requests:

1. **Check Existing Issues** - Avoid duplicates
2. **Provide Context** - Explain the use case
3. **Consider Implementation** - Suggest how it might work
4. **Benefits** - Explain why this would be valuable

## 🔧 Pull Requests

### Before Submitting
- [ ] Code follows project style guidelines
- [ ] Changes have been tested thoroughly
- [ ] Documentation has been updated if needed
- [ ] No sensitive data (tokens, keys) in commits

### PR Process
1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Keep changes focused and atomic
   - Test thoroughly

3. **Submit PR**
   - Clear title and description
   - Reference related issues
   - Include testing details

### PR Review
- Maintainers will review within 48 hours
- Address feedback constructively
- Update PR based on review comments

## 📚 Documentation

Help improve documentation:
- Fix typos and unclear instructions
- Add examples and use cases
- Improve setup guides
- Update API documentation

## 🏗️ Project Structure

```
TeleTube/
├── yt_downloader_bot.py     # Main bot script
├── requirements.txt         # Python dependencies
├── setup.bat/.sh           # Setup scripts
├── .env.example            # Configuration template
├── README.md               # Project overview
├── SETUP_GUIDE.md          # Detailed setup guide
├── CONTRIBUTING.md         # This file
├── LICENSE                 # Project license
├── ffmpeg/                 # FFmpeg binaries
├── downloads/              # Temporary downloads
└── api_server/             # Local API server files
```

## 🚫 What Not to Contribute

- Copyrighted content or code
- Changes that violate YouTube's ToS
- Malicious or harmful code
- Personal configuration files (.env, logs)

## 🤝 Code of Conduct

- Be respectful and inclusive
- Help newcomers learn
- Provide constructive feedback
- Focus on the code, not the person

## 📞 Getting Help

- **Documentation**: Check README and setup guides first
- **Issues**: Search existing issues before creating new ones
- **Discussions**: Use GitHub Discussions for questions
- **Security**: Email security issues privately

## 🏆 Recognition

Contributors will be:
- Added to the contributors list
- Credited in release notes
- Mentioned in significant feature announcements

Thank you for contributing to TeleTube! 🎉
