import asyncio
import asyncio
import os
import re
import tempfile
import subprocess
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
        
        # FFmpeg path setup
        self.ffmpeg_path = self._get_ffmpeg_path()
    
    def _get_ffmpeg_path(self) -> str:
        """Get FFmpeg executable path"""
        # Check if we have local FFmpeg installation
        local_ffmpeg = Path("ffmpeg-8.0-essentials_build/bin/ffmpeg.exe")
        if local_ffmpeg.exists():
            return str(local_ffmpeg.resolve())
        
        # Fallback to system FFmpeg
        return "ffmpeg"
    
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
    
    async def _post_process_with_ffmpeg(self, input_path: str, max_size_mb: int) -> Optional[str]:
        """Post-process video with FFmpeg for better compatibility"""
        if not Path(input_path).exists():
            return None
            
        try:
            output_path = input_path.replace('.webm', '_processed.mp4').replace('.mkv', '_processed.mp4')
            if output_path == input_path:
                output_path = input_path.replace('.mp4', '_processed.mp4')
            
            # FFmpeg command for conversion and optimization
            cmd = [
                self.ffmpeg_path,
                '-i', input_path,
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-movflags', '+faststart',
                '-y',  # Overwrite output file
                output_path
            ]
            
            def _run_ffmpeg():
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=300)
                    return output_path
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                    logger.error(f"FFmpeg processing failed: {e}")
                    return input_path  # Return original file if FFmpeg fails
            
            loop = asyncio.get_event_loop()
            processed_path = await loop.run_in_executor(None, _run_ffmpeg)
            
            # Check if processing was successful and file size is acceptable
            if Path(processed_path).exists():
                file_size = Path(processed_path).stat().st_size / (1024 * 1024)
                if file_size <= max_size_mb:
                    # Remove original file if processing was successful
                    if processed_path != input_path and Path(input_path).exists():
                        Path(input_path).unlink()
                    return processed_path
                else:
                    # If processed file is too large, remove it and return original
                    if processed_path != input_path:
                        Path(processed_path).unlink()
                    return input_path
            
            return input_path
            
        except Exception as e:
            logger.error(f"FFmpeg post-processing error: {e}")
            return input_path  # Return original file on any error


class YouTubeDownloader(BaseVideoDownloader):
    """Скачивание видео с YouTube"""
    
    def __init__(self, download_dir: str = "downloads"):
        super().__init__(download_dir)
        # Основные настройки для максимальной совместимости
        self.base_opts = {
            'outtmpl': str(self.download_dir / '%(title)s_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            # Ключевые настройки для обхода блокировок
            'extractor_args': {
                'youtube': {
                    'skip': ['dash'],  # Пропускаем DASH форматы
                    'player_skip': ['js'],  # Пропускаем JS плеер
                    'comment_sort': ['top'],
                    'max_comments': [0],  # Не загружаем комментарии
                }
            },
            # Паузы между запросами
            'sleep_interval_requests': 1,
            'sleep_interval': 0,
            'max_sleep_interval': 5,
            # Отключаем ненужные функции
            'writesubtitles': False,
            'writeautomaticsub': False,
            'writeinfojson': False,
            'writethumbnail': False,
            # Настройки сети
            'socket_timeout': 30,
            'retries': 3,
        }
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о YouTube видео"""
        try:
            def _extract_info():
                # Используем те же настройки, что и для скачивания
                info_opts = self.base_opts.copy()
                info_opts.update({
                    'cookiesfrombrowser': ('chrome', None, None, None),
                    'http_headers': {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept': '*/*',
                        'Accept-Language': 'en-US,en;q=0.9',
                    },
                })
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
        """Скачать YouTube видео с реалистичными ожиданиями"""
        # Простая но эффективная стратегия с FFmpeg поддержкой
        strategies = [
            self._download_with_ffmpeg_ytdlp,
            self._download_basic_with_latest_ytdlp,
            self._download_with_android_client,
            self._download_minimal_fallback
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logger.info(f"Trying YouTube strategy {i}/{len(strategies)}: {strategy.__name__}")
                filepath = await strategy(url, max_size_mb)
                if filepath and Path(filepath).exists():
                    logger.info(f"YouTube video downloaded successfully with {strategy.__name__}: {filepath}")
                    
                    # Apply FFmpeg post-processing for better compatibility
                    processed_filepath = await self._post_process_with_ffmpeg(filepath, max_size_mb)
                    return processed_filepath
            except Exception as e:
                logger.warning(f"Strategy {i} ({strategy.__name__}) failed: {e}")
                if i == len(strategies):  # Last strategy failed
                    error_msg = str(e).lower()
                    if "sign in" in error_msg or "bot" in error_msg:
                        raise VideoDownloadError(f"YouTube bot detection: {e}")
                    else:
                        raise VideoDownloadError(f"All strategies failed: {e}")
                continue
        
        return None
    
    async def _download_with_ffmpeg_ytdlp(self, url: str, max_size_mb: int) -> Optional[str]:
        """Новая стратегия: Использование yt-dlp с FFmpeg обработкой"""
        opts = {
            'format': f'worst[filesize<{max_size_mb}M]/worst',
            'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ffmpeg_location': self.ffmpeg_path,
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }],
            'extract_flat': False,
            'writeinfojson': False,
        }
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                info = ydl.extract_info(url, download=False)
                if info:
                    # Find the downloaded file
                    for file_path in self.download_dir.glob(f"*{info.get('id', '')}*"):
                        if file_path.is_file() and file_path.suffix in ['.mp4', '.webm', '.mkv']:
                            return str(file_path)
                return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)
    
    async def _download_with_basic_settings(self, url: str, max_size_mb: int) -> Optional[str]:
        """Первая стратегия: базовые настройки"""
        opts = self.base_opts.copy()
        opts['format'] = f'best[height<=720][filesize<{max_size_mb}M]/best[filesize<{max_size_mb}M]'
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                info = ydl.extract_info(url, download=False)
                filename = ydl.prepare_filename(info)
                return filename
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)
    
    async def _download_with_cookies_from_browser(self, url: str, max_size_mb: int) -> Optional[str]:
        """Стратегия 2: Быстрое использование cookies из браузера"""
        # Пробуем использовать cookies только если есть доступ
        try:
            opts = self.base_opts.copy()
            opts.update({
                'format': f'best[height<=720][filesize<{max_size_mb}M]/best',
                'cookiesfrombrowser': ('chrome',),
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Origin': 'https://www.youtube.com',
                    'Referer': 'https://www.youtube.com/',
                },
            })
            
            def _download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                    info = ydl.extract_info(url, download=False)
                    return ydl.prepare_filename(info)
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _download)
            
        except Exception as e:
            # Если cookies недоступны, пробуем без них
            logger.warning(f"Cookie access failed, trying without cookies: {e}")
            opts = self.base_opts.copy()
            opts.update({
                'format': f'best[height<=720][filesize<{max_size_mb}M]/best',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Origin': 'https://www.youtube.com',
                    'Referer': 'https://www.youtube.com/',
                },
            })
            
            def _download():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                    info = ydl.extract_info(url, download=False)
                    return ydl.prepare_filename(info)
            
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, _download)
    
    async def _download_with_android_client(self, url: str, max_size_mb: int) -> Optional[str]:
        """Стратегия 1: Android клиент API с агрессивными настройками"""
        opts = {
            'format': f'best[height<=720][filesize<{max_size_mb}M]/worst',
            'outtmpl': str(self.download_dir / '%(title)s_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_music', 'android', 'web'],
                    'skip': ['dash', 'hls'],
                    'innertube_host': 'youtubei.googleapis.com',
                    'innertube_key': None,
                    'visitor_data': None,
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.apps.youtube.music/5.16.51 (Linux; U; Android 11) gzip',
                'X-YouTube-Client-Name': '21',
                'X-YouTube-Client-Version': '5.16.51',
                'Content-Type': 'application/json',
            },
            'sleep_interval': 1,
            'socket_timeout': 30,
        }
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                info = ydl.extract_info(url, download=False)
                return ydl.prepare_filename(info)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)
    
    async def _download_with_ios_client(self, url: str, max_size_mb: int) -> Optional[str]:
        """Стратегия 3: iOS клиент API с специальными настройками"""
        opts = {
            'format': f'best[height<=480][filesize<{max_size_mb}M]/worst',
            'outtmpl': str(self.download_dir / '%(title)s_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'mweb'],
                    'skip': ['dash', 'hls'],
                    'innertube_host': 'youtubei.googleapis.com',
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.ios.youtube/19.09.3 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X; en_US)',
                'X-YouTube-Client-Name': '5',
                'X-YouTube-Client-Version': '19.09.3',
                'Content-Type': 'application/json',
            },
            'sleep_interval': 2,
            'socket_timeout': 30,
        }
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                info = ydl.extract_info(url, download=False)
                return ydl.prepare_filename(info)
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)
    
    async def _download_basic_fallback(self, url: str, max_size_mb: int) -> Optional[str]:
        """Стратегия 4: Минимальные настройки (крайняя мера)"""
        opts = {
            'format': 'worst',
            'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,  # Не игнорируем ошибки
            'no_color': True,
        }
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:  # Проверяем, что info не None
                    ydl.download([url])
                    filename = ydl.prepare_filename(info)
                    return filename
                return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)
    
    async def _download_basic_with_latest_ytdlp(self, url: str, max_size_mb: int) -> Optional[str]:
        """Стратегия 1: Обновленный yt-dlp с базовыми настройками"""
        opts = {
            'format': f'worst[filesize<{max_size_mb}M]/worst',
            'outtmpl': str(self.download_dir / '%(title)s_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'writeinfojson': False,
            'writethumbnail': False,
            'writesubtitles': False,
        }
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                info = ydl.extract_info(url, download=False)
                if info:
                    return ydl.prepare_filename(info)
                return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _download)
    
    async def _download_minimal_fallback(self, url: str, max_size_mb: int) -> Optional[str]:
        """Стратегия 3: Минимальные настройки"""
        opts = {
            'format': 'worst',
            'outtmpl': str(self.download_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'extract_flat': False,
        }
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    ydl.download([url])
                    return ydl.prepare_filename(info)
                return None
        
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
            dirname_pattern=str(self.download_dir),
            # Add better error handling and retry logic
            max_connection_attempts=3,
            request_timeout=60,
            # Reduce rate limiting
            sleep=True,
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
        """Скачать Instagram видео с фолбэком на yt-dlp"""
        # Сначала пробуем yt-dlp (часто работает лучше)
        try:
            return await self._download_with_ytdlp(url, max_size_mb)
        except Exception as e:
            logger.warning(f"yt-dlp failed for Instagram, trying instaloader: {e}")
            # Фолбэк на оригинальный метод
            return await self._download_with_instaloader(url, max_size_mb)
    
    async def _download_with_ytdlp(self, url: str, max_size_mb: int) -> Optional[str]:
        """Скачать Instagram через yt-dlp"""
        opts = {
            'format': f'best[filesize<{max_size_mb}M]/best',
            'outtmpl': str(self.download_dir / '%(title)s_%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
            },
        }
        
        def _download():
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([url])
                info = ydl.extract_info(url, download=False)
                if info:
                    return ydl.prepare_filename(info)
                return None
        
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, _download)
        
        if filepath and Path(filepath).exists():
            logger.info(f"Instagram video downloaded via yt-dlp: {filepath}")
            return filepath
        return None
    
    async def _download_with_instaloader(self, url: str, max_size_mb: int) -> Optional[str]:
        """Оригинальный метод через instaloader"""
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
                
                logger.info(f"Instagram video downloaded via instaloader: {filepath}")
                return filepath
            
        except Exception as e:
            logger.error(f"Error downloading Instagram video with instaloader: {e}")
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
            # Enhanced anti-detection for TikTok
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            },
            'sleep_interval': 2,
            'max_sleep_interval': 5,
            'socket_timeout': 30,
            'retries': 3,
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
