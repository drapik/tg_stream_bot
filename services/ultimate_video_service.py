import yt_dlp
import os
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Tuple
from loguru import logger


class UltimateVideoService:
    """
    Ultimate video download service using the latest yt-dlp.
    Works completely autonomously without requiring manual cookie setup.
    
    Implements proven strategies to maximize YouTube download success:
    1. Latest yt-dlp extractor arguments
    2. Multiple client API emulation (Android, iOS, Web)
    3. Enhanced anti-detection headers
    4. Automatic fallback strategies
    5. Timeout controls and resource management
    
    Designed for remote/server deployment - no local browser interaction needed.
    """
    
    def __init__(self, base_temp_dir: str = "temp"):
        self.base_temp_dir = Path(base_temp_dir)
        self.base_temp_dir.mkdir(exist_ok=True)
        
        logger.info("Ultimate Video Service initialized - autonomous operation mode")
    
    async def download_video(self, url: str, chat_id: int, max_size_mb: int = 50) -> Tuple[Optional[str], Optional[str]]:
        """
        Downloads a video from a given URL (YouTube, Instagram, TikTok).
        Returns a tuple (file_path, video_title) on success, (None, None) on failure.
        
        Uses multiple strategies to handle various platform restrictions.
        
        Args:
            url: Video URL
            chat_id: Telegram chat ID for unique temp directory
            max_size_mb: Maximum file size in MB
            
        Returns:
            Tuple[file_path, video_title] or (None, None) on failure
        """
        # Create a unique temporary directory for each chat to avoid file conflicts
        chat_temp_dir = self.base_temp_dir / str(chat_id)
        chat_temp_dir.mkdir(exist_ok=True)
        
        output_template = str(chat_temp_dir / "%(title).50s.%(ext)s")
        
        # Multiple download strategies - NO COOKIES REQUIRED
        strategies = [
            self._download_with_latest_ytdlp,
            self._download_with_android_client,
            self._download_with_ios_client,
            self._download_with_enhanced_web_client,
            self._download_with_tv_client,
            self._download_minimal_fallback
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logger.info(f"Trying download strategy {i}/{len(strategies)}: {strategy.__name__}")
                filepath, title = await strategy(url, output_template, chat_temp_dir, max_size_mb)
                if filepath and Path(filepath).exists():
                    logger.info(f"Video downloaded successfully with {strategy.__name__}: {filepath}")
                    return filepath, title
            except Exception as e:
                logger.warning(f"Strategy {i} ({strategy.__name__}) failed: {e}")
                # Clean up any partial files from failed attempt
                self._cleanup_partial_files(chat_temp_dir)
                
                if i == len(strategies):  # Last strategy failed
                    error_msg = str(e).lower()
                    if "sign in" in error_msg or "bot" in error_msg:
                        logger.warning(f"YouTube bot detection: {e}")
                    elif "cookie" in error_msg:
                        logger.warning(f"Cookie authentication failed: {e}")
                    else:
                        logger.error(f"All download strategies failed: {e}")
                continue
        
        return None, None
    
    async def _download_with_latest_ytdlp(self, url: str, output_template: str, chat_temp_dir: Path, max_size_mb: int) -> Tuple[Optional[str], Optional[str]]:
        """Strategy 1: Latest yt-dlp with optimal settings (NO COOKIES NEEDED)"""
        ydl_opts = {
            'format': f'best[height<=720][filesize<{max_size_mb}M]/worst',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'retries': 3,
            # Latest extractor arguments for 2024/2025
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios', 'android_creator'],
                    'skip': ['dash', 'hls'],
                    'comment_sort': ['top'],
                    'max_comments': [0],
                }
            },
            # Modern browser headers
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Origin': 'https://www.youtube.com',
                'Referer': 'https://www.youtube.com/',
            },
            'socket_timeout': 20,
            'sleep_interval_requests': 1,
        }
        
        logger.info("Using latest yt-dlp with iOS/Android Creator clients")
        return await self._execute_download(ydl_opts, url, chat_temp_dir, max_size_mb)
    
    async def _download_with_tv_client(self, url: str, output_template: str, chat_temp_dir: Path, max_size_mb: int) -> Tuple[Optional[str], Optional[str]]:
        """Strategy 5: YouTube TV client API (often bypasses restrictions)"""
        ydl_opts = {
            'format': f'worst[filesize<{max_size_mb}M]/worst',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'retries': 2,
            'extractor_args': {
                'youtube': {
                    'player_client': ['tv_embedded'],
                    'skip': ['dash', 'hls'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (SMART-TV; Linux; Tizen 2.4.0) AppleWebkit/538.1 (KHTML, like Gecko) SamsungBrowser/1.1 TV Safari/538.1',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
            },
            'socket_timeout': 15,
        }
        
        logger.info("Using YouTube TV client API")
        return await self._execute_download(ydl_opts, url, chat_temp_dir, max_size_mb)
    
    async def _download_with_android_client(self, url: str, output_template: str, chat_temp_dir: Path, max_size_mb: int) -> Tuple[Optional[str], Optional[str]]:
        """Strategy 2: Android client API with enhanced settings (PROVEN TO WORK)"""
        ydl_opts = {
            'format': f'best[height<=720][filesize<{max_size_mb}M]/worst',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'retries': 2,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android_music', 'android'],
                    'skip': ['dash', 'hls'],
                    # Remove problematic innertube settings that cause network errors
                    'comment_sort': ['top'],
                    'max_comments': [0],
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.apps.youtube.music/5.16.51 (Linux; U; Android 11) gzip',
                'X-YouTube-Client-Name': '21',
                'X-YouTube-Client-Version': '5.16.51',
                'Content-Type': 'application/json',
            },
            # Network timeouts for responsiveness
            'socket_timeout': 15,
            'sleep_interval_requests': 1,
            'sleep_interval': 0,
            'max_sleep_interval': 3,
        }
        
        logger.info("Using Android Music client API (enhanced strategy)")
        return await self._execute_download(ydl_opts, url, chat_temp_dir, max_size_mb)
    
    async def _download_with_ios_client(self, url: str, output_template: str, chat_temp_dir: Path, max_size_mb: int) -> Tuple[Optional[str], Optional[str]]:
        """Strategy 3: iOS client API with special settings (PROVEN TO WORK)"""
        ydl_opts = {
            'format': f'best[height<=480][filesize<{max_size_mb}M]/worst',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['ios'],
                    'skip': ['dash', 'hls'],
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.ios.youtube/19.09.3 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X; en_US)',
                'X-YouTube-Client-Name': '5',
                'X-YouTube-Client-Version': '19.09.3',
            },
            'socket_timeout': 10,
            'retries': 1,
        }
        
        logger.info("Using iOS client API (proven strategy)")
        return await self._execute_download(ydl_opts, url, chat_temp_dir, max_size_mb)
    
    async def _download_with_enhanced_web_client(self, url: str, output_template: str, chat_temp_dir: Path, max_size_mb: int) -> Tuple[Optional[str], Optional[str]]:
        """Strategy 4: Enhanced web client with latest anti-detection"""
        ydl_opts = {
            'format': f'worst[filesize<{max_size_mb}M]/worst',
            'outtmpl': output_template,
            'quiet': True,
            'no_warnings': True,
            'noplaylist': True,
            'retries': 2,
            'extractor_args': {
                'youtube': {
                    'player_client': ['web'],
                    'skip': ['dash'],
                    'player_skip': ['js'],
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Origin': 'https://www.youtube.com',
                'Referer': 'https://www.youtube.com/',
            },
            'socket_timeout': 15,
        }
        
        logger.info("Using enhanced web client")
        return await self._execute_download(ydl_opts, url, chat_temp_dir, max_size_mb)
    
    async def _download_minimal_fallback(self, url: str, output_template: str, chat_temp_dir: Path, max_size_mb: int) -> Tuple[Optional[str], Optional[str]]:
        """Strategy 6: Minimal settings with ID-only filename (last resort)"""
        ydl_opts = {
            'format': 'worst',
            'outtmpl': str(chat_temp_dir / '%(id)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': False,
            'no_color': True,
            'noplaylist': True,
            # Absolute minimal settings to avoid detection
            'writesubtitles': False,
            'writeautomaticsub': False,
            'writeinfojson': False,
            'writethumbnail': False,
            'writecomments': False,
            'writedescription': False,
            'writeannotations': False,
            'retries': 1,
            'socket_timeout': 10,
        }
        
        logger.info("Using minimal fallback settings (last resort)")
        return await self._execute_download(ydl_opts, url, chat_temp_dir, max_size_mb)
    
    async def _execute_download(self, ydl_opts: dict, url: str, chat_temp_dir: Path, max_size_mb: int) -> Tuple[Optional[str], Optional[str]]:
        """Execute the actual download with given options and timeout"""
        def _download():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Download and extract video info
                info_dict = ydl.extract_info(url, download=True)
                
                # Find the actual downloaded file
                for file in chat_temp_dir.glob("*"):
                    if file.is_file() and file.suffix.lower() in ['.mp4', '.mkv', '.webm', '.avi']:
                        # Check file size
                        file_size_mb = file.stat().st_size / (1024 * 1024)
                        if file_size_mb <= max_size_mb:
                            return str(file), info_dict.get('title', 'video')
                        else:
                            logger.warning(f"File too large: {file_size_mb:.2f}MB > {max_size_mb}MB")
                            file.unlink()  # Remove oversized file
                            return None, None
                
                # Fallback: use prepared filename
                video_path = ydl.prepare_filename(info_dict)
                if Path(video_path).exists():
                    return video_path, info_dict.get('title', 'video')
                
                return None, None
        
        # Run in executor with timeout
        loop = asyncio.get_event_loop()
        try:
            # 15 second timeout for each strategy
            return await asyncio.wait_for(
                loop.run_in_executor(None, _download),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.warning("Download strategy timed out after 15 seconds")
            # Clean up any partial files
            self._cleanup_partial_files(chat_temp_dir)
            raise Exception("Download timeout")
    
    def _cleanup_partial_files(self, chat_temp_dir: Path):
        """Clean up any partial files from failed downloads"""
        try:
            for file in chat_temp_dir.glob("*"):
                if file.is_file():
                    file.unlink()
        except Exception as e:
            logger.warning(f"Error cleaning up partial files: {e}")
    
    async def get_video_info(self, url: str) -> Optional[dict]:
        """Extract video information without downloading using autonomous strategies."""
        
        # Strategy 1: Latest yt-dlp with optimal settings
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extractor_args': {
                    'youtube': {
                        'player_client': ['ios', 'android_creator'],
                        'skip': ['dash', 'hls'],
                    }
                },
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                },
            }
            
            def _extract_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            loop = asyncio.get_event_loop()
            info_dict = await loop.run_in_executor(None, _extract_info)
            
            if info_dict:
                logger.info("Video info extracted successfully")
                return self._format_video_info(info_dict)
                
        except Exception as e:
            logger.warning(f"Video info extraction failed: {e}")
        
        return None
    
    def _format_video_info(self, info_dict: dict) -> dict:
        """Format video info dictionary"""
        return {
            'title': info_dict.get('title', 'Unknown'),
            'duration': info_dict.get('duration', 0),
            'uploader': info_dict.get('uploader', 'Unknown'),
            'view_count': info_dict.get('view_count', 0),
            'id': info_dict.get('id', ''),
        }
    
    def cleanup_chat_files(self, chat_id: int):
        """
        Clean up all files for a specific chat.
        
        Args:
            chat_id: Telegram chat ID
        """
        chat_temp_dir = self.base_temp_dir / str(chat_id)
        if chat_temp_dir.exists():
            try:
                for file in chat_temp_dir.rglob("*"):
                    if file.is_file():
                        file.unlink()
                chat_temp_dir.rmdir()
                logger.info(f"Cleaned up files for chat {chat_id}")
            except Exception as e:
                logger.error(f"Error cleaning up files for chat {chat_id}: {e}")
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """
        Clean up old temporary files.
        
        Args:
            max_age_hours: Maximum age of files in hours
        """
        import time
        current_time = time.time()
        
        for chat_dir in self.base_temp_dir.iterdir():
            if chat_dir.is_dir():
                try:
                    for file in chat_dir.rglob("*"):
                        if file.is_file():
                            file_age = current_time - file.stat().st_mtime
                            if file_age > max_age_hours * 3600:
                                file.unlink()
                                logger.info(f"Removed old file: {file}")
                    
                    # Remove empty directories
                    if not any(chat_dir.iterdir()):
                        chat_dir.rmdir()
                        logger.info(f"Removed empty directory: {chat_dir}")
                        
                except Exception as e:
                    logger.error(f"Error cleaning up directory {chat_dir}: {e}")


# Global service instance
ultimate_video_service = UltimateVideoService()