# 🎬 Video Download Bot

A comprehensive Telegram bot for downloading videos from popular platforms (YouTube, Instagram, TikTok) with automatic format optimization and seamless chat integration.

## 🌟 Features

### ✅ Currently Implemented
- **Multi-Platform Support**: YouTube, Instagram, TikTok
- **Automatic URL Detection**: Just send a video link!
- **Smart Format Selection**: Optimized for Telegram's 50MB limit
- **Video Information Display**: Shows title, uploader, duration
- **Progressive Status Updates**: Real-time download progress
- **Auto-Cleanup**: Removes temporary files after sending
- **Role-Based Access**: User whitelist and admin controls
- **Persistent User Registry**: Remembers usernames across restarts

### 🎯 Platform Support

| Platform | URL Types | Max Size | Features |
|----------|-----------|----------|----------|
| **YouTube** | `youtube.com/watch`, `youtu.be`, `youtube.com/shorts` | 50MB | HD quality up to 720p |
| **Instagram** | `instagram.com/p/`, `instagram.com/reel/` | 50MB | Reels and video posts |
| **TikTok** | `tiktok.com/@user/video/`, `vm.tiktok.com` | 50MB | All TikTok videos |

## 🚀 Usage

### Basic Commands
- `/start` - Welcome message and bot introduction
- `/help` - Show all available commands and platforms
- `/version` - Display bot version
- `/download <URL>` - Download video from URL

### Admin Commands (Admin only)
- `/users` - Show whitelist users with their nicknames

### Automatic URL Detection
Just send any supported video URL to the bot and it will automatically:
1. Detect the platform
2. Extract video information  
3. Download and optimize the video
4. Send it back as a playable video file

## 🔧 Technical Architecture

### Core Components

1. **Platform Detection System** (`PlatformDetector`)
   - Regex-based URL pattern matching
   - Supports multiple URL formats per platform
   - Extensible for new platforms

2. **Modular Downloader Architecture**
   - `BaseVideoDownloader` - Abstract base class
   - `YouTubeDownloader` - Uses yt-dlp for YouTube content
   - `InstagramDownloader` - Uses instaloader for Instagram
   - `TikTokDownloader` - Uses yt-dlp for TikTok content

3. **Main Service** (`GetVideoStreamContentService`)
   - Unified interface for all platforms
   - Automatic platform routing
   - Error handling and logging
   - File size management

### Download Process Flow

```
User sends URL → Platform Detection → Get Video Info → Download Video → 
Validate Size → Send to Telegram → Cleanup Files
```

### Error Handling
- **Platform Not Supported**: Clear message with supported platforms
- **Video Too Large**: Size limit notification
- **Download Failed**: Specific error messages
- **Network Issues**: Retry mechanisms in yt-dlp/instaloader

## 🛠️ Dependencies

### Core Libraries
- `aiogram==3.7.0` - Telegram Bot API framework
- `yt-dlp>=2024.9.27` - YouTube and TikTok downloading
- `instaloader==4.10.3` - Instagram content downloading
- `aiofiles~=23.2.1` - Async file operations
- `loguru==0.7.2` - Advanced logging

### System Requirements
- Python 3.12+
- 50MB+ free disk space for temporary files
- Internet connection
- Telegram Bot Token

## 📁 Project Structure

```
tg_stream_bot/
├── services/
│   └── getvideostreamcontent.py    # 🆕 Complete video downloading system
├── commands/
│   ├── basic.py                    # ✏️ Enhanced with video commands
│   └── admin.py                    # Existing admin functionality
├── utils/
│   └── user_registry.py            # User nickname persistence
├── data/                           # 🆕 Persistent user data
├── downloads/                      # 🆕 Temporary video storage
├── requirements.txt                # ✏️ Updated with new dependencies
└── .gitignore                      # ✏️ Excludes downloads and user data
```

## 🔐 Security & Privacy

### User Data Protection
- Downloads stored temporarily and auto-deleted
- User registry data excluded from version control
- No video content permanently stored
- Whitelist-based access control

### Platform Compliance
- Respects platform rate limits
- Uses official APIs where possible
- Downloads only publicly available content
- Proper attribution in video captions

## 🚦 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
Create `.env` file:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
```

### 3. Configure Users
Edit `config.py`:
```python
WHITELIST = {
    123456789: "admin",    # Your Telegram ID
    987654321: "user",     # Other user IDs
}
```

### 4. Run the Bot
```bash
python bot.py
```

## 💡 Usage Examples

### Simple Video Download
```
User: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Bot: ⏳ Скачиваю видео с YouTube...
     📹 Rick Astley - Never Gonna Give You Up
     👤 Rick Astley
     ⏱️ 213s
     
     📤 Отправляю видео (15.2MB)...
     [Sends video file]
```

### Command-Based Download  
```
User: /download https://instagram.com/p/ABC123/
Bot: [Same process as above]
```

### Multiple URLs Detection
```
User: Check out these videos: 
      https://youtube.com/watch?v=123
      https://tiktok.com/@user/video/456
Bot: 🎬 Найдено несколько видео:
     1. Youtube: https://youtube.com/watch?v=123...
     2. Tiktok: https://tiktok.com/@user/video/456...
     
     💡 Отправьте ссылку отдельным сообщением для скачивания
```

## 🔄 Future Enhancements

### Ready for Groups
The current architecture is designed to work in:
- ✅ Private chats (current)
- 🔄 Group chats (ready to implement)
- 🔄 Channels (ready to implement)

### Planned Features
- [ ] Batch download support
- [ ] Audio extraction (MP3)
- [ ] Custom quality selection
- [ ] Download queuing system
- [ ] Usage statistics for admins
- [ ] Playlist support
- [ ] More platforms (Twitter, Reddit, etc.)

## 🐛 Troubleshooting

### Common Issues

**"Unsupported platform"**
- Check if URL format is correct
- Ensure platform is in supported list

**"File too large"**
- Video exceeds 50MB Telegram limit
- Bot automatically tries lower quality

**"Download failed"**
- Check internet connection
- Video might be private or deleted
- Platform may have rate limits

### Logs
Check `logs/bot.log` for detailed error information.

## 📊 Performance

### Typical Download Times
- **YouTube (720p, 10MB)**: 15-30 seconds
- **Instagram (Reel, 5MB)**: 10-20 seconds  
- **TikTok (Standard, 3MB)**: 5-15 seconds

### Resource Usage
- **Memory**: ~50-100MB during download
- **Storage**: Temporary files auto-deleted
- **Network**: Depends on video size

---

**Version**: 1.0.0 with Video Download Support  
**Last Updated**: September 2025