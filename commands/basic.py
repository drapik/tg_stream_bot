from aiogram import Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from decorators import role_required
from config import VERSION, WHITELIST
from utils import update_user_registry
from services.working_final_service import WorkingFinalService
from pathlib import Path
import asyncio
import re
from loguru import logger


# Initialize working final service - accepts platform reality but still tries
video_service = WorkingFinalService()


class PlatformDetector:
    """Simple platform detector for pure FFmpeg service"""
    
    @staticmethod
    def detect_platform(url: str) -> str:
        """Detect platform from URL"""
        url_lower = url.lower()
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        else:
            return None


def extract_urls_from_text(text: str) -> list[str]:
    """Извлечь все URL из текста сообщения"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    return urls


@role_required("user")
async def start_handler(message: types.Message):
    """Обработчик команды /start"""
    # Обновляем реестр информацией о пользователе
    update_user_registry(message.from_user)
    
    await message.answer(
        "👋 Привет! Я автоматически скачиваю видео с YouTube, Instagram и TikTok.\n\n"
        "💡 Просто отправьте ссылку на видео!",
        parse_mode="Markdown"
    )


@role_required("user")
async def version_handler(message: types.Message):
    """Обработчик команды /version"""
    # Обновляем реестр информацией о пользователе
    update_user_registry(message.from_user)
    
    await message.answer(f"Версия бота: {VERSION}")


@role_required("user")
async def help_handler(message: types.Message):
    """Обработчик команды /help"""
    # Обновляем реестр информацией о пользователе
    update_user_registry(message.from_user)
    
    user_id = message.from_user.id
    user_role = WHITELIST.get(user_id, "user")
    
    help_text = "🤖 **Доступные команды:**\n\n"
    
    # Базовые команды для всех пользователей
    help_text += "📋 **Основные команды:**\n"
    help_text += "/start - Запуск бота и приветствие\n"
    help_text += "/help - Показать это сообщение\n"
    help_text += "/version - Версия бота\n\n"
    
    help_text += "🎬 **Автоматическое скачивание видео**\n"
    help_text += "Поддерживаемые платформы: YouTube, Instagram, TikTok\n"
    help_text += "💡 Просто отправьте ссылку на видео\n\n"
    
    # Админские команды только для админов
    if user_role == "admin":
        help_text += "🛡️ **Админские команды:**\n"
        help_text += "/users - Список пользователей в whitelist\n\n"
    
    help_text += "ℹ️ Ваша роль: **" + user_role + "**"
    
    await message.answer(help_text, parse_mode="Markdown")


@role_required("user")
async def message_handler(message: types.Message):
    """Обработчик обычных сообщений для автоматического обнаружения видео"""
    # Обновляем реестр информацией о пользователе
    update_user_registry(message.from_user)
    
    # Ищем URL в тексте сообщения
    if not message.text:
        return
    
    urls = extract_urls_from_text(message.text)
    
    # Проверяем каждый URL на соответствие паттернам
    for url in urls:
        platform = PlatformDetector.detect_platform(url)
        if platform:
            # Молчаливо скачиваем видео
            await process_video_download(message, url)
            break  # Обрабатываем только первую подходящую ссылку


async def process_video_download(message: types.Message, url: str):
    """Молчаливое скачивание и отправка видео с yt-dlp + FFmpeg
    Обрабатывает YouTube bot detection молча (это ожидаемое поведение)
    """
    platform = PlatformDetector.detect_platform(url)
    if not platform:
        return  # Молча игнорируем неподдерживаемые ссылки
    
    try:
        # Скачиваем видео с working final сервисом - принимает реальность платформ
        logger.info(f"Downloading {platform} video with working final service: {url}")
        filepath = await video_service.download_video(url, max_size_mb=50)
        
        if filepath and Path(filepath).exists():
            file_size = Path(filepath).stat().st_size / (1024 * 1024)  # MB
            logger.info(f"Video download successful: {file_size:.2f} MB")
            
            # Проверяем размер файла
            if file_size > 50:
                Path(filepath).unlink()  # Удаляем слишком большой файл
                logger.warning(f"File too large ({file_size:.2f} MB), removed")
                return
            
            # Отправляем видео без лишних сообщений
            video_file = FSInputFile(filepath)
            await message.answer_video(video=video_file)
            logger.info(f"Video sent successfully to user {message.from_user.id}")
            
            # Удаляем скачанный файл
            Path(filepath).unlink()
            logger.info("Downloaded file cleaned up")
        else:
            # Молча игнорируем неудачные загрузки (обычно YouTube bot detection)
            logger.warning(f"Video download failed for {url} - likely YouTube bot detection (expected)")
            return
    
    except Exception as e:
        # Молча игнорируем любые ошибки - полностью молчаливый режим
        error_msg = str(e).lower()
        if "sign in" in error_msg or "bot" in error_msg:
            logger.warning(f"YouTube bot detection for {url} (expected behavior)")
        else:
            logger.error(f"Video download error for {url}: {e}")
        return


def register_basic_commands(dp: Dispatcher):
    """Регистрация базовых команд"""
    dp.message(Command("start"))(start_handler)
    dp.message(Command("version"))(version_handler)
    dp.message(Command("help"))(help_handler)
    
    # Регистрируем обработчик обычных сообщений (для автоматического обнаружения ссылок)
    dp.message()(message_handler)
