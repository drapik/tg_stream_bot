import asyncio
import asyncio
import os
import re
import tempfile
import aiofiles
from pathlib import Path
from typing import Dict, Any, Optional, Union
from loguru import logger
import yt_dlp
import instaloader
from urllib.parse import urlparse


class VideoDownloadError(Exception):
    """Исключение для ошибок скачивания видео"""
    pass


class PlatformDetector:
    """Детектор платформы по URL"""
    
    YOUTUBE_PATTERNS = [
        r'youtube\.com/watch\?v=',
        r'youtu\.be/',
        r'youtube\.com/shorts/',
        r'm\.youtube\.com/watch\?v='
    ]
    
    INSTAGRAM_PATTERNS = [
        r'instagram\.com/p/',
        r'instagram\.com/reel/',
        r'instagram\.com/tv/',
        r'instagr\.am/p/'
    ]
    
    TIKTOK_PATTERNS = [
        r'tiktok\.com/@[^/]+/video/',
        r'vm\.tiktok\.com/',
        r'vt\.tiktok\.com/'
    ]
    
    @classmethod
    def detect_platform(cls, url: str) -> Optional[str]:
        """Определить платформу по URL"""
        url_lower = url.lower()
        
        for pattern in cls.YOUTUBE_PATTERNS:
            if re.search(pattern, url_lower):
                return 'youtube'
                
        for pattern in cls.INSTAGRAM_PATTERNS:
            if re.search(pattern, url_lower):
                return 'instagram'
                
        for pattern in cls.TIKTOK_PATTERNS:
            if re.search(pattern, url_lower):
                return 'tiktok'
                
        return None


class BaseVideoDownloader:
    """Базовый класс для скачивания видео"""
    
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о видео"""
        raise NotImplementedError
    
    async def download_video(self, url: str, max_size_mb: int = 50) -> Optional[str]:
        """Скачать видео"""
        raise NotImplementedError
    
    def _generate_filename(self, title: str, video_id: str, ext: str = "mp4") -> str:
        """Генерация безопасного имени файла"""
        # Очистка названия от недопустимых символов
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title)[:50]
        return f"{safe_title}_{video_id}.{ext}"


class YouTubeDownloader(BaseVideoDownloader):
    """Скачивание видео с YouTube"""
    
    def __init__(self, download_dir: str = "downloads"):
        super().__init__(download_dir)
        self.ydl_opts = {
            'format': 'best[height<=720][filesize<50M]/best[filesize<50M]',
            'outtmpl': str(self.download_dir / '%(title)s_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            # Anti-bot detection settings
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            # Additional anti-detection settings
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls']  # Skip DASH and HLS formats that might be more restricted
                }
            },
            # Sleep between requests to avoid rate limiting
            'sleep_interval': 1,
            'max_sleep_interval': 5,
            # Try to use the best available format without forcing specific quality
            'format_sort': ['res:720', 'ext:mp4:m4a'],
        }
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о YouTube видео"""
        try:
            def _extract_info():
                # Use the same improved settings for info extraction
                info_opts = {
                    'quiet': True,
                    'http_headers': self.ydl_opts['http_headers'],
                    'sleep_interval': 1,
                }
                with yt_dlp.YoutubeDL(info_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _extract_info)
            
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'id': info.get('id', ''),
                'platform': 'youtube'
            }
        except Exception as e:
            logger.error(f"Error getting YouTube video info: {e}")
            return None
    
    async def download_video(self, url: str, max_size_mb: int = 50) -> Optional[str]:
        """Скачать YouTube видео"""
        # Simplified strategy: try basic approach, then minimal
        strategies = [
            self._download_with_basic_settings,
            self._download_with_minimal_settings,
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logger.info(f"Trying YouTube download strategy {i}/{len(strategies)}")
                filepath = await strategy(url, max_size_mb)
                if filepath and Path(filepath).exists():
                    logger.info(f"YouTube video downloaded successfully with strategy {i}: {filepath}")
                    return filepath
            except Exception as e:
                logger.warning(f"Strategy {i} failed: {e}")
                if i == len(strategies):  # Last strategy failed
                    # Check if it's a bot detection error
                    error_msg = str(e).lower()
                    if "sign in" in error_msg or "bot" in error_msg:
                        raise VideoDownloadError(f"YouTube bot detection: {e}")
                    else:
                        raise VideoDownloadError(f"All strategies failed: {e}")
                continue
        
        return None
    
    async def _download_with_basic_settings(self, url: str, max_size_mb: int) -> Optional[str]:
        """Первая стратегия: базовые настройки"""
        opts = self.ydl_opts.copy()
        opts['format'] = f'best[height<=720][filesize<{max_size_mb}M]/best[filesize<{max_size_mb}M]'
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                info = ydl.extract_info(url, download=False)
                filename = ydl.prepare_filename(info)
                return filename
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)
    
    async def _download_with_mobile_headers(self, url: str, max_size_mb: int) -> Optional[str]:
        """Вторая стратегия: мобильные заголовки"""
        opts = {
            'format': f'worst[height<=360][filesize<{max_size_mb}M]/worst[filesize<{max_size_mb}M]',
            'outtmpl': str(self.download_dir / '%(title)s_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
            },
            'sleep_interval': 3,
            'max_sleep_interval': 8,
        }
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                info = ydl.extract_info(url, download=False)
                filename = ydl.prepare_filename(info)
                return filename
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)
    
    async def _download_with_minimal_settings(self, url: str, max_size_mb: int) -> Optional[str]:
        """Третья стратегия: минимальные настройки"""
        opts = {
            'format': 'worst',  # Просто самое низкое качество
            'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),  # Простое имя файла
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'skip': ['dash', 'hls'],
                    'player_skip': ['configs', 'webpage'],
                    'comment_sort': ['top'],
                }
            },
        }
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                info = ydl.extract_info(url, download=False)
                filename = ydl.prepare_filename(info)
                return filename
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)


class InstagramDownloader(BaseVideoDownloader):
    """Скачивание видео с Instagram"""
    
    def __init__(self, download_dir: str = "downloads"):
        super().__init__(download_dir)
        self.loader = instaloader.Instaloader(
            download_videos=True,
            download_pictures=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            dirname_pattern=str(self.download_dir)
        )
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Получить информацию об Instagram видео"""
        try:
            shortcode = self._extract_shortcode(url)
            if not shortcode:
                return None
            
            def _get_post():
                return instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            loop = asyncio.get_event_loop()
            post = await loop.run_in_executor(None, _get_post)
            
            return {
                'title': post.caption[:100] if post.caption else f"Instagram post {shortcode}",
                'duration': post.video_duration if post.is_video else 0,
                'uploader': post.owner_username,
                'view_count': post.video_view_count if post.is_video else 0,
                'id': shortcode,
                'platform': 'instagram'
            }
        except Exception as e:
            logger.error(f"Error getting Instagram post info: {e}")
            return None
    
    async def download_video(self, url: str, max_size_mb: int = 50) -> Optional[str]:
        """Скачать Instagram видео"""
        try:
            shortcode = self._extract_shortcode(url)
            if not shortcode:
                raise VideoDownloadError("Invalid Instagram URL")
            
            def _download():
                post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
                if not post.is_video:
                    raise VideoDownloadError("Post is not a video")
                
                # Скачиваем видео
                self.loader.download_post(post, target=str(self.download_dir))
                
                # Ищем скачанный видеофайл
                pattern = f"*{shortcode}.mp4"
                video_files = list(self.download_dir.glob(pattern))
                
                if video_files:
                    return str(video_files[0])
                return None
            
            loop = asyncio.get_event_loop()
            filepath = await loop.run_in_executor(None, _download)
            
            if filepath and Path(filepath).exists():
                # Проверяем размер файла
                file_size = Path(filepath).stat().st_size / (1024 * 1024)  # MB
                if file_size > max_size_mb:
                    Path(filepath).unlink()  # Удаляем слишком большой файл
                    raise VideoDownloadError(f"File too large: {file_size:.1f}MB > {max_size_mb}MB")
                
                logger.info(f"Instagram video downloaded: {filepath}")
                return filepath
            
        except Exception as e:
            logger.error(f"Error downloading Instagram video: {e}")
            raise VideoDownloadError(f"Failed to download Instagram video: {e}")
        
        return None
    
    def _extract_shortcode(self, url: str) -> Optional[str]:
        """Извлечь shortcode из Instagram URL"""
        patterns = [
            r'/p/([A-Za-z0-9_-]+)/',
            r'/reel/([A-Za-z0-9_-]+)/',
            r'/tv/([A-Za-z0-9_-]+)/'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None


class TikTokDownloader(BaseVideoDownloader):
    """Скачивание видео с TikTok"""
    
    def __init__(self, download_dir: str = "downloads"):
        super().__init__(download_dir)
        self.ydl_opts = {
            'format': 'best[height<=720][filesize<50M]',
            'outtmpl': str(self.download_dir / '%(title)s_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            # Anti-bot detection settings for TikTok
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            },
            'sleep_interval': 1,
            'max_sleep_interval': 3,
        }
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о TikTok видео"""
        try:
            def _extract_info():
                info_opts = {
                    'quiet': True,
                    'http_headers': self.ydl_opts['http_headers'],
                    'sleep_interval': 1,
                }
                with yt_dlp.YoutubeDL(info_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _extract_info)
            
            return {
                'title': info.get('title', 'TikTok Video')[:100],
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'id': info.get('id', ''),
                'platform': 'tiktok'
            }
        except Exception as e:
            logger.error(f"Error getting TikTok video info: {e}")
            return None
    
    async def download_video(self, url: str, max_size_mb: int = 50) -> Optional[str]:
        """Скачать TikTok видео"""
        try:
            opts = self.ydl_opts.copy()
            opts['format'] = f'best[height<=720][filesize<{max_size_mb}M]'
            
            def _download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                    info = ydl.extract_info(url, download=False)
                    filename = ydl.prepare_filename(info)
                    return filename
            
            loop = asyncio.get_event_loop()
            filepath = await loop.run_in_executor(None, _download)
            
            if filepath and Path(filepath).exists():
                logger.info(f"TikTok video downloaded: {filepath}")
                return filepath
            
        except Exception as e:
            logger.error(f"Error downloading TikTok video: {e}")
            raise VideoDownloadError(f"Failed to download TikTok video: {e}")
        
        return None


class GetVideoStreamContentService:
    """Главный сервис для скачивания видео с разных платформ"""
    
    def __init__(self, download_dir: str = "downloads"):
        """Инициализация сервиса"""
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # Инициализируем загрузчики для каждой платформы
        self.downloaders = {
            'youtube': YouTubeDownloader(download_dir),
            'instagram': InstagramDownloader(download_dir),
            'tiktok': TikTokDownloader(download_dir)
        }
    
    async def download_video(self, url: str, max_size_mb: int = 50) -> Optional[str]:
        """
        Скачать видео по URL с любой поддерживаемой платформы
        
        Args:
            url: URL видео для скачивания
            max_size_mb: Максимальный размер файла в MB
            
        Returns:
            Путь к скачанному файлу или None в случае ошибки
        """
        platform = PlatformDetector.detect_platform(url)
        
        if not platform:
            logger.warning(f"Unsupported platform for URL: {url}")
            raise VideoDownloadError("Unsupported platform")
        
        if platform not in self.downloaders:
            logger.error(f"No downloader available for platform: {platform}")
            raise VideoDownloadError(f"No downloader for {platform}")
        
        logger.info(f"Downloading {platform} video from URL: {url}")
        
        try:
            downloader = self.downloaders[platform]
            filepath = await downloader.download_video(url, max_size_mb)
            return filepath
        except Exception as e:
            logger.error(f"Error downloading video from {platform}: {e}")
            raise
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Получить информацию о видео
        
        Args:
            url: URL видео
            
        Returns:
            Словарь с информацией о видео или None
        """
        platform = PlatformDetector.detect_platform(url)
        
        if not platform or platform not in self.downloaders:
            logger.warning(f"Unsupported platform for URL: {url}")
            return None
        
        logger.info(f"Getting {platform} video info for URL: {url}")
        
        try:
            downloader = self.downloaders[platform]
            info = await downloader.get_video_info(url)
            return info
        except Exception as e:
            logger.error(f"Error getting video info from {platform}: {e}")
            return None
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Очистка старых скачанных файлов"""
        import time
        current_time = time.time()
        
        for file_path in self.download_dir.iterdir():
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_hours * 3600:  # часы в секунды
                    try:
                        file_path.unlink()
                        logger.info(f"Removed old file: {file_path}")
                    except Exception as e:
                        logger.error(f"Error removing file {file_path}: {e}")
