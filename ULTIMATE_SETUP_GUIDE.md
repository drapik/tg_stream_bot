# Ultimate Video Download Bot Setup Guide

This guide will help you set up the Telegram bot with the latest working video download functionality.

## 🔧 Prerequisites

### 1. Python 3.12+ 
Make sure you have Python 3.12 or later installed.

### 2. FFmpeg Installation
FFmpeg is CRUCIAL for video processing and merging. Install it according to your system:

#### Windows:
1. Download FFmpeg from https://ffmpeg.org/download.html
2. Extract to a folder (e.g., `C:\ffmpeg`)
3. Add `C:\ffmpeg\bin` to your system PATH
4. Test: Open command prompt and run `ffmpeg -version`

#### macOS:
```bash
# Using Homebrew
brew install ffmpeg

# Or using MacPorts
port install ffmpeg
```

#### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Linux (CentOS/RHEL):
```bash
sudo yum install ffmpeg
# or
sudo dnf install ffmpeg
```

### 3. Verify FFmpeg Installation
Run this command to verify FFmpeg is properly installed:
```bash
ffmpeg -version
```

You should see FFmpeg version information.

## 📦 Installation Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

This will install:
- `aiogram==3.7.0` (Telegram Bot API)
- `yt-dlp>=2025.9.5` (Latest video downloader)
- `python-dotenv==1.0.1` (Environment variables)
- `aiofiles~=23.2.1` (Async file operations)
- `aiohttp==3.9.5` (HTTP client)
- `loguru==0.7.2` (Logging)
- `instaloader` (Instagram support)
- Plus testing dependencies

### 2. Environment Setup
Create a `.env` file in the project root:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
ADMIN_IDS=your_user_id,another_admin_id
LOG_LEVEL=INFO
```

Get your bot token from [@BotFather](https://t.me/botfather) on Telegram.

### 3. Browser Cookies Setup (CRITICAL for YouTube)
This step is essential for bypassing YouTube's bot detection:

#### Method 1: Browser Extension (Recommended)
1. Install a cookie export extension:
   - **Chrome**: "Get cookies.txt LOCALLY"
   - **Firefox**: "cookies.txt"
2. Visit YouTube while logged in to your account
3. Click the extension and export cookies for `youtube.com`
4. Save the file as `cookies.txt` in the project root directory

#### Method 2: Manual Export
1. Open browser developer tools (F12)
2. Navigate to YouTube while logged in
3. Go to Application/Storage → Cookies → https://youtube.com
4. Copy all cookies and save in Netscape cookie format as `cookies.txt`

#### Verify Cookies Setup
Run the cookie checker:
```bash
python setup_cookies.py
```

### 4. Configure User Access
Edit `config.py` to add authorized users:
```python
WHITELIST = {
    123456789: "admin",    # Replace with your Telegram user ID
    987654321: "user",     # Replace with other user IDs
}
```

To find your Telegram user ID:
1. Message [@userinfobot](https://t.me/userinfobot)
2. Copy the ID number

## 🚀 Running the Bot

### Standard Run:
```bash
python bot.py
```

### Docker Run (Optional):
```bash
# Build and run with docker-compose
docker-compose up -d

# Or build manually
docker build -t tg_stream_bot .
docker run -d --name tg_stream_bot tg_stream_bot
```

## 🎯 Features

### Supported Platforms:
- **YouTube** (youtube.com, youtu.be, youtube.com/shorts)
- **Instagram** (instagram.com/p/, /reel/, /tv/)
- **TikTok** (tiktok.com, vm.tiktok.com)

### How It Works:
1. Send a message containing a video URL
2. Bot automatically detects supported platforms
3. Downloads video using latest yt-dlp with authentication
4. Sends video file to chat
5. Automatically cleans up temporary files

### Commands:
- `/start` - Welcome message and setup info
- `/help` - Detailed help and commands
- `/version` - Show bot version
- `/users` - List authorized users (admin only)

## 🔍 Troubleshooting

### Common Issues:

#### "Download failed" messages:
1. **Check FFmpeg**: Run `ffmpeg -version`
2. **Update yt-dlp**: `pip install -U yt-dlp`
3. **Verify cookies**: Run `python setup_cookies.py`
4. **Check video accessibility**: Try the URL in your browser

#### YouTube bot detection:
1. **Essential**: Set up `cookies.txt` from a logged-in session
2. Use fresh cookies (export new ones regularly)
3. Some videos may still be unavailable due to restrictions

#### Permission errors:
1. Check file permissions on temp directory
2. Ensure bot has write access to project directory

#### Large file errors:
- Bot limits files to 50MB (Telegram limit)
- Videos exceeding this will not be sent

### Debug Mode:
Edit `config.py` and set:
```python
LOG_LEVEL = "DEBUG"
```

Check logs in `logs/bot.log` for detailed error information.

## 🔐 Security Notes

1. **Never commit cookies.txt** - It's already in `.gitignore`
2. **Keep bot token secret** - Use environment variables
3. **Regularly update cookies** - Export fresh ones periodically
4. **Limit user access** - Only add trusted users to WHITELIST

## 📊 Performance Tips

1. **Fresh cookies**: Update cookies.txt regularly
2. **System resources**: Ensure adequate disk space for temp files
3. **Network**: Stable internet connection improves success rates
4. **FFmpeg**: Use latest version for best compatibility

## 🆘 Support

If you encounter issues:

1. Check the logs: `logs/bot.log`
2. Run cookie checker: `python setup_cookies.py`
3. Verify FFmpeg: `ffmpeg -version`
4. Update dependencies: `pip install -r requirements.txt --upgrade`

## 🎉 Success!

Once set up correctly, your bot will:
- ✅ Automatically detect video URLs in messages
- ✅ Download videos with authentication
- ✅ Handle multiple platforms seamlessly
- ✅ Provide user-friendly error messages
- ✅ Clean up temporary files automatically

The implementation uses your tested working function with enhancements for the aiogram framework and better error handling.