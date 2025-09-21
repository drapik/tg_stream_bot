from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from decorators import role_required
from config import VERSION, WHITELIST
from utils import update_user_registry
from services.ultimate_video_service import ultimate_video_service
from pathlib import Path
import re
from loguru import logger


def extract_urls_from_text(text: str) -> list[str]:
    """Extract all URLs from message text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return urls


def is_supported_platform(url: str) -> bool:
    """Check if URL is from a supported platform"""
    url_lower = url.lower()
    supported_patterns = [
        'youtube.com', 'youtu.be', 'youtube.com/shorts',  # YouTube
        'instagram.com', 'instagr.am',  # Instagram
        'tiktok.com', 'vm.tiktok.com', 'vt.tiktok.com'  # TikTok
    ]
    return any(pattern in url_lower for pattern in supported_patterns)


@role_required("user")
async def start_handler(message: types.Message):
    """Handler for /start command"""
    update_user_registry(message.from_user)
    
    await message.answer(
        "👋 Hello! I automatically download videos from YouTube, Instagram, and TikTok.\n\n"
        "💡 Just send me a video link!\n\n"
        "📋 Supported platforms:\n"
        "• YouTube (youtube.com, youtu.be)\n"
        "• Instagram (instagram.com)\n"
        "• TikTok (tiktok.com)\n\n"
        "🔧 Commands:\n"
        "/start - Show this message\n"
        "/version - Show bot version\n"
        "/help - Show detailed help",
        parse_mode="Markdown"
    )


@role_required("user") 
async def version_handler(message: types.Message):
    """Handler for /version command"""
    update_user_registry(message.from_user)
    await message.answer(f"Bot version: {VERSION}")


@role_required("user")
async def help_handler(message: types.Message):
    """Handler for /help command"""
    update_user_registry(message.from_user)
    
    user_id = message.from_user.id
    user_role = WHITELIST.get(user_id, "user")
    
    help_text = "🤖 **Available Commands:**\n\n"
    
    # Basic commands for all users
    help_text += "📋 **Basic Commands:**\n"
    help_text += "/start - Start bot and show welcome message\n"
    help_text += "/help - Show this help message\n"
    help_text += "/version - Show bot version\n\n"
    
    help_text += "🎬 **Automatic Video Download**\n"
    help_text += "Supported platforms: YouTube, Instagram, TikTok\n"
    help_text += "💡 Just send a video link and I'll download it for you!\n\n"
    
    help_text += "🔧 **Requirements:**\n"
    help_text += "• FFmpeg must be installed and in PATH\n"
    help_text += "• Latest yt-dlp version (2025.9.5+)\n"
    help_text += "• Optional: cookies.txt for better authentication\n\n"
    
    # Admin commands only for admins
    if user_role == "admin":
        help_text += "🛡️ **Admin Commands:**\n"
        help_text += "/users - List users in whitelist\n\n"
    
    help_text += f"ℹ️ Your role: **{user_role}**"
    
    await message.answer(help_text, parse_mode="Markdown")


@role_required("user")
async def message_handler(message: types.Message):
    """Handler for regular messages with automatic video URL detection"""
    update_user_registry(message.from_user)
    
    # Check if message contains text
    if not message.text:
        return
    
    # Extract URLs from message text
    urls = extract_urls_from_text(message.text)
    
    # Process each supported URL
    for url in urls:
        if is_supported_platform(url):
            await process_video_download(message, url)
            break  # Process only the first supported URL


async def process_video_download(message: types.Message, url: str):
    """
    Process video download using the ultimate video service.
    Implements the working function you provided with aiogram integration.
    """
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        logger.info(f"Starting video download for user {user_id}, URL: {url}")
        
        # Send "typing" action to show the bot is working
        await message.bot.send_chat_action(chat_id, "upload_video")
        
        # Download video using your tested function
        file_path, video_title = await ultimate_video_service.download_video(url, chat_id)
        
        if file_path and Path(file_path).exists():
            logger.info(f"Video downloaded successfully: {file_path}")
            
            # Get file size for logging
            file_size = Path(file_path).stat().st_size / (1024 * 1024)  # MB
            logger.info(f"File size: {file_size:.2f} MB")
            
            # Send the video file to the chat
            video_file = FSInputFile(file_path)
            
            # Create caption with video title
            caption = f"🎬 {video_title}" if video_title else "🎬 Downloaded Video"
            if len(caption) > 1024:  # Telegram caption limit
                caption = caption[:1021] + "..."
            
            await message.answer_video(
                video=video_file,
                caption=caption
            )
            
            logger.info(f"Video sent successfully to chat {chat_id}")
            
            # Clean up: delete the downloaded video file and temp directory
            try:
                Path(file_path).unlink()
                ultimate_video_service.cleanup_chat_files(chat_id)
                logger.info("Downloaded file and temp directory cleaned up")
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {cleanup_error}")
                
        else:
            # Send user-friendly error message
            await message.answer(
                "❌ Download failed. This video may be unavailable or the link might be invalid.\n\n"
                "💡 Tips:\n"
                "• Make sure the video is public\n"
                "• Try a different video\n"
                "• Some videos may be restricted",
                parse_mode="Markdown"
            )
            logger.warning(f"Video download failed for URL: {url}")
            
    except Exception as e:
        logger.error(f"Error processing video download: {e}")
        
        # Send user-friendly error message
        await message.answer(
            "❌ An error occurred while downloading the video.\n\n"
            "💡 This might be due to:\n"
            "• Video restrictions or bot detection\n"
            "• Network issues\n"
            "• Video format not supported\n\n"
            "Please try again with a different video.",
            parse_mode="Markdown"
        )
        
        # Clean up any partial files
        try:
            ultimate_video_service.cleanup_chat_files(chat_id)
        except Exception as cleanup_error:
            logger.error(f"Error during error cleanup: {cleanup_error}")


def register_ultimate_commands(dp: Dispatcher):
    """Register commands using the ultimate video service"""
    dp.message(Command("start"))(start_handler)
    dp.message(Command("version"))(version_handler)
    dp.message(Command("help"))(help_handler)
    
    # Register message handler for automatic URL detection
    dp.message()(message_handler)