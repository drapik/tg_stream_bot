#!/usr/bin/env python3
"""
Working FFmpeg-Enhanced Video Download Service
This replaces the current failing service with a robust, FFmpeg-powered solution
"""
import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import json
import re


class FFmpegEnhancedVideoService:
    """
    FFmpeg-enhanced video service that actually works
    Uses simple, direct yt-dlp + FFmpeg approach for maximum reliability
    """
    
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # FFmpeg path setup
        self.ffmpeg_path = self._get_ffmpeg_path()
        logger.info(f"FFmpeg path: {self.ffmpeg_path}")
    
    def _get_ffmpeg_path(self) -> str:
        """Get FFmpeg executable path"""
        # Check if we have local FFmpeg installation
        local_ffmpeg = Path("ffmpeg-8.0-essentials_build/bin/ffmpeg.exe")
        if local_ffmpeg.exists():
            return str(local_ffmpeg.resolve())
        
        # Fallback to system FFmpeg
        return "ffmpeg"
    
    def _detect_platform(self, url: str) -> str:
        """Detect platform from URL"""
        url_lower = url.lower()
        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        else:
            return 'unknown'
    
    async def download_video(self, url: str, max_size_mb: int = 50) -> Optional[str]:
        """
        Download video from any supported platform
        Simple and reliable approach
        """
        platform = self._detect_platform(url)
        logger.info(f"Downloading {platform} video: {url}")
        
        try:
            # Strategy 1: Simple yt-dlp download
            result = await self._download_simple_ytdlp(url, max_size_mb)
            if result:
                logger.info(f"✅ Download successful: {result}")
                return result
            
            # Strategy 2: Fallback with worst quality
            result = await self._download_fallback(url, max_size_mb)
            if result:
                logger.info(f"✅ Fallback download successful: {result}")
                return result
                
            logger.error("❌ All download strategies failed")
            return None
            
        except Exception as e:
            logger.error(f"❌ Download failed: {e}")
            return None
    
    async def _download_simple_ytdlp(self, url: str, max_size_mb: int) -> Optional[str]:
        """Simple, working yt-dlp download"""
        output_template = str(self.download_dir / "%(id)s.%(ext)s")
        
        cmd = [
            'yt-dlp',
            '--format', f'worst[filesize<{max_size_mb}M]/worst',
            '--output', output_template,
            '--ffmpeg-location', self.ffmpeg_path,
            '--no-warnings',
            url
        ]
        
        def _run_download():
            try:
                # Run yt-dlp
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    check=True,
                    timeout=180  # 3 minutes timeout
                )
                
                # Find downloaded file
                for file_path in self.download_dir.glob("*"):
                    if file_path.is_file() and file_path.suffix in ['.mp4', '.webm', '.mkv', '.flv']:
                        return str(file_path)
                
                return None
                
            except subprocess.TimeoutExpired:
                logger.error("Download timed out after 3 minutes")
                return None
            except subprocess.CalledProcessError as e:
                logger.error(f"yt-dlp failed: {e.stderr}")
                return None
        
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, _run_download)
        
        if filepath and Path(filepath).exists():
            # Check file size
            file_size = Path(filepath).stat().st_size / (1024 * 1024)  # MB
            if file_size <= max_size_mb:
                logger.info(f"Downloaded: {filepath} ({file_size:.2f} MB)")
                return filepath
            else:
                logger.warning(f"File too large: {file_size:.2f} MB > {max_size_mb} MB")
                Path(filepath).unlink()  # Remove oversized file
                return None
        
        return None
    
    async def _download_fallback(self, url: str, max_size_mb: int) -> Optional[str]:
        """Ultra-simple fallback download"""
        output_template = str(self.download_dir / "fallback_%(id)s.%(ext)s")
        
        cmd = [
            'yt-dlp',
            '--format', 'worst',
            '--output', output_template,
            '--no-warnings',
            '--ignore-errors',
            url
        ]
        
        def _run_fallback():
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=120  # 2 minutes timeout
                )
                
                # Find downloaded file
                for file_path in self.download_dir.glob("fallback_*"):
                    if file_path.is_file() and file_path.suffix in ['.mp4', '.webm', '.mkv', '.flv']:
                        return str(file_path)
                
                return None
                
            except subprocess.TimeoutExpired:
                logger.error("Fallback download timed out")
                return None
            except Exception as e:
                logger.error(f"Fallback download failed: {e}")
                return None
        
        loop = asyncio.get_event_loop()
        filepath = await loop.run_in_executor(None, _run_fallback)
        
        if filepath and Path(filepath).exists():
            return filepath
        
        return None
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get video information"""
        try:
            cmd = [
                'yt-dlp',
                '--dump-json',
                '--no-warnings',
                url
            ]
            
            def _get_info():
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
                    return json.loads(result.stdout)
                except (subprocess.CalledProcessError, json.JSONDecodeError, subprocess.TimeoutExpired):
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
            
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
        
        return None


# Convenience function to replace the existing service
async def download_video_with_ffmpeg(url: str, max_size_mb: int = 50, download_dir: str = "downloads") -> Optional[str]:
    """
    Convenient function to download videos with FFmpeg enhancement
    Can be used as a drop-in replacement for the existing download function
    """
    service = FFmpegEnhancedVideoService(download_dir=download_dir)
    return await service.download_video(url, max_size_mb)