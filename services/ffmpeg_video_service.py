import asyncio
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import re
import json
import os


class FFmpegVideoDownloader:
    """
    FFmpeg-based video downloader that's more reliable than pure Python solutions
    Uses yt-dlp + FFmpeg combination for maximum compatibility
    """
    
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # Set up FFmpeg path
        self.ffmpeg_path = self._get_ffmpeg_path()
        self._check_dependencies()
    
    def _get_ffmpeg_path(self) -> str:
        """Get FFmpeg executable path"""
        # Check if we have local FFmpeg installation
        local_ffmpeg = Path("ffmpeg-8.0-essentials_build/bin/ffmpeg.exe")
        if local_ffmpeg.exists():
            return str(local_ffmpeg.resolve())
        
        # Fallback to system FFmpeg
        return "ffmpeg"
    
    def _check_dependencies(self):
        """Check if required dependencies are available"""
        try:
            # Check yt-dlp
            subprocess.run(['yt-dlp', '--version'], 
                         capture_output=True, check=True)
            logger.info("yt-dlp is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("yt-dlp not found. Please install: pip install yt-dlp")
            raise RuntimeError("yt-dlp is required")
        
        try:
            # Check FFmpeg with our path
            result = subprocess.run([self.ffmpeg_path, '-version'], 
                                  capture_output=True, check=True)
            logger.info(f"FFmpeg is available at: {self.ffmpeg_path}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error(f"FFmpeg not found at: {self.ffmpeg_path}")
            raise RuntimeError("FFmpeg is required")
    
    async def download_video(self, url: str, max_size_mb: int = 50) -> Optional[str]:
        """
        Download video using FFmpeg-based approach
        """
        platform = self._detect_platform(url)
        logger.info(f"Downloading {platform} video: {url}")
        
        strategies = [
            self._download_with_ytdlp_ffmpeg,
            self._download_direct_stream,
            self._download_with_fallback
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                logger.info(f"Trying FFmpeg strategy {i}/{len(strategies)}: {strategy.__name__}")
                result = await strategy(url, max_size_mb)
                if result:
                    logger.info(f"Successfully downloaded with {strategy.__name__}: {result}")
                    return result
            except Exception as e:
                logger.warning(f"Strategy {i} failed: {e}")
                if i == len(strategies):
                    raise
        
        return None
    
    async def _download_with_ytdlp_ffmpeg(self, url: str, max_size_mb: int) -> Optional[str]:
        """
        Primary strategy: Use yt-dlp with FFmpeg (simplified and working)
        """
        output_template = str(self.download_dir / "%(id)s.%(ext)s")
        
        cmd = [
            'yt-dlp',
            '--format', f'worst[ext=mp4]/best[filesize<{max_size_mb}M]/worst',
            '--output', output_template,
            '--ffmpeg-location', self.ffmpeg_path,
            '--no-warnings',
            '--quiet',
            url
        ]
        
        def _run_command():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=120)
                
                # Find the downloaded file
                for file_path in self.download_dir.glob("*"):
                    if file_path.is_file() and file_path.suffix in ['.mp4', '.webm', '.mkv']:
                        return str(file_path)
                
                return None
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logger.error(f"yt-dlp command failed: {e}")
                raise
        
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, _run_command)
        
        if filepath and Path(filepath).exists():
            # Verify file size
            file_size = Path(filepath).stat().st_size / (1024 * 1024)  # MB
            if file_size > max_size_mb:
                Path(filepath).unlink()
                raise Exception(f"File too large: {file_size:.1f}MB > {max_size_mb}MB")
            
            logger.info(f"Downloaded: {filepath} ({file_size:.2f} MB)")
            return filepath
        
        return None
    
    async def _download_direct_stream(self, url: str, max_size_mb: int) -> Optional[str]:
        """
        Secondary strategy: Direct stream capture with FFmpeg
        """
        # First, get stream info with yt-dlp
        info_cmd = [
            'yt-dlp', 
            '--dump-json',
            '--no-warnings',
            url
        ]
        
        def _get_stream_info():
            try:
                result = subprocess.run(info_cmd, capture_output=True, text=True, check=True)
                return json.loads(result.stdout)
            except (subprocess.CalledProcessError, json.JSONDecodeError) as e:
                logger.error(f"Failed to get stream info: {e}")
                raise
        
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _get_stream_info)
        
        if not info or 'url' not in info:
            raise Exception("No stream URL found")
        
        # Use FFmpeg to download directly
        output_file = self.download_dir / f"{info.get('id', 'video')}.mp4"
        
        ffmpeg_cmd = [
            self.ffmpeg_path,
            '-i', info['url'],
            '-c', 'copy',
            '-avoid_negative_ts', 'make_zero',
            '-y',  # Overwrite output file
            str(output_file)
        ]
        
        def _run_ffmpeg():
            try:
                subprocess.run(ffmpeg_cmd, capture_output=True, check=True)
                return str(output_file)
            except subprocess.CalledProcessError as e:
                logger.error(f"FFmpeg failed: {e.stderr}")
                raise
        
        filepath = await loop.run_in_executor(None, _run_ffmpeg)
        
        if filepath and Path(filepath).exists():
            file_size = Path(filepath).stat().st_size / (1024 * 1024)  # MB
            if file_size > max_size_mb:
                Path(filepath).unlink()
                raise Exception(f"File too large: {file_size:.1f}MB > {max_size_mb}MB")
            
            return filepath
        
        return None
    
    async def _download_with_fallback(self, url: str, max_size_mb: int) -> Optional[str]:
        """
        Fallback strategy: Simplest possible download
        """
        output_template = str(self.download_dir / "%(id)s.%(ext)s")
        
        cmd = [
            'yt-dlp',
            '--format', 'worst',  # Get anything that works
            '--output', output_template,
            '--no-warnings',
            url
        ]
        
        def _run_simple():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=60)
                
                # Find the downloaded file
                for file_path in self.download_dir.glob("*"):
                    if file_path.is_file() and file_path.suffix in ['.mp4', '.webm', '.mkv', '.flv']:
                        return str(file_path)
                
                return None
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                logger.error(f"Simple yt-dlp failed: {e}")
                raise
        
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, _run_simple)
        
        if filepath and Path(filepath).exists():
            return filepath
        
        return None
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'instagram.com' in url:
            return 'instagram'
        elif 'tiktok.com' in url:
            return 'tiktok'
        else:
            return 'unknown'
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get video information"""
        cmd = [
            'yt-dlp',
            '--dump-json',
            '--no-warnings',
            url
        ]
        
        def _get_info():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return json.loads(result.stdout)
            except (subprocess.CalledProcessError, json.JSONDecodeError):
                return None
        
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(None, _get_info)
        
        if info:
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'id': info.get('id', ''),
                'platform': self._detect_platform(url)
            }
        
        return None


class FFmpegVideoService:
    """
    Unified service using FFmpeg approach for all platforms
    """
    
    def __init__(self, download_dir: str = "downloads"):
        self.downloader = FFmpegVideoDownloader(download_dir)
    
    async def download_video(self, url: str, max_size_mb: int = 50) -> Optional[str]:
        """Download video from any supported platform"""
        try:
            return await self.downloader.download_video(url, max_size_mb)
        except Exception as e:
            logger.error(f"FFmpeg video download failed for {url}: {e}")
            raise
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get video information"""
        try:
            return await self.downloader.get_video_info(url)
        except Exception as e:
            logger.error(f"Failed to get video info for {url}: {e}")
            return None