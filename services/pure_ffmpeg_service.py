#!/usr/bin/env python3
"""
Pure FFmpeg Video Download Service
No yt-dlp, no Python libraries - just FFmpeg doing everything
"""
import asyncio
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger
import re


class PureFFmpegVideoService:
    """
    Pure FFmpeg-based video service
    FFmpeg handles everything: downloading, processing, format conversion
    """
    
    def __init__(self, download_dir: str = "downloads"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(exist_ok=True)
        
        # FFmpeg path setup
        self.ffmpeg_path = self._get_ffmpeg_path()
        logger.info(f"Using pure FFmpeg at: {self.ffmpeg_path}")
        
        # Verify FFmpeg works
        self._verify_ffmpeg()
    
    def _get_ffmpeg_path(self) -> str:
        """Get FFmpeg executable path"""
        # Check local FFmpeg installation first
        local_ffmpeg = Path("ffmpeg-8.0-essentials_build/bin/ffmpeg.exe")
        if local_ffmpeg.exists():
            return str(local_ffmpeg.resolve())
        
        # Fallback to system FFmpeg
        return "ffmpeg"
    
    def _verify_ffmpeg(self):
        """Verify FFmpeg is working"""
        try:
            result = subprocess.run(
                [self.ffmpeg_path, '-version'], 
                capture_output=True, 
                text=True, 
                check=True,
                timeout=10
            )
            logger.info("✅ FFmpeg verification successful")
        except Exception as e:
            logger.error(f"❌ FFmpeg verification failed: {e}")
            raise RuntimeError("FFmpeg is not available or not working")
    
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
        Download video using pure FFmpeg
        FFmpeg can handle most video URLs directly
        """
        platform = self._detect_platform(url)
        logger.info(f"Downloading {platform} video with pure FFmpeg: {url}")
        
        try:
            # Strategy 1: Direct FFmpeg download
            result = await self._download_direct_ffmpeg(url, max_size_mb)
            if result:
                logger.info(f"✅ Direct FFmpeg download successful: {result}")
                return result
            
            # Strategy 2: FFmpeg with format specification
            result = await self._download_with_format_selection(url, max_size_mb)
            if result:
                logger.info(f"✅ FFmpeg with format selection successful: {result}")
                return result
            
            # Strategy 3: FFmpeg with user agent and headers
            result = await self._download_with_headers(url, max_size_mb)
            if result:
                logger.info(f"✅ FFmpeg with headers successful: {result}")
                return result
            
            logger.error("❌ All pure FFmpeg strategies failed")
            return None
            
        except Exception as e:
            logger.error(f"❌ Pure FFmpeg download failed: {e}")
            return None
    
    async def _download_direct_ffmpeg(self, url: str, max_size_mb: int) -> Optional[str]:
        """Strategy 1: Direct FFmpeg download - simplest approach"""
        output_file = self.download_dir / f"video_{hash(url) % 100000}.mp4"
        
        cmd = [
            self.ffmpeg_path,
            '-i', url,
            '-c', 'copy',  # Copy without re-encoding for speed
            '-y',  # Overwrite output file
            str(output_file)
        ]
        
        return await self._run_ffmpeg_command(cmd, output_file, max_size_mb)
    
    async def _download_with_format_selection(self, url: str, max_size_mb: int) -> Optional[str]:
        """Strategy 2: FFmpeg with format selection"""
        output_file = self.download_dir / f"video_fmt_{hash(url) % 100000}.mp4"
        
        cmd = [
            self.ffmpeg_path,
            '-i', url,
            '-c:v', 'libx264',  # Re-encode video for compatibility
            '-c:a', 'aac',      # Re-encode audio for compatibility
            '-preset', 'fast',  # Fast encoding
            '-crf', '23',       # Good quality
            '-movflags', '+faststart',  # Web optimization
            '-y',
            str(output_file)
        ]
        
        return await self._run_ffmpeg_command(cmd, output_file, max_size_mb)
    
    async def _download_with_headers(self, url: str, max_size_mb: int) -> Optional[str]:
        """Strategy 3: FFmpeg with HTTP headers for better compatibility"""
        output_file = self.download_dir / f"video_hdr_{hash(url) % 100000}.mp4"
        
        cmd = [
            self.ffmpeg_path,
            '-user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            '-referer', url,
            '-i', url,
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-preset', 'ultrafast',  # Fastest encoding
            '-crf', '28',  # Lower quality for smaller size
            '-movflags', '+faststart',
            '-y',
            str(output_file)
        ]
        
        return await self._run_ffmpeg_command(cmd, output_file, max_size_mb)
    
    async def _run_ffmpeg_command(self, cmd: list, output_file: Path, max_size_mb: int) -> Optional[str]:
        """Run FFmpeg command with proper error handling"""
        
        def _execute():
            try:
                logger.info(f"Running FFmpeg: {' '.join(cmd[:5])}...")  # Log first few args
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 minutes timeout
                    check=False   # Don't raise on non-zero exit
                )
                
                if result.returncode == 0:
                    if output_file.exists():
                        file_size = output_file.stat().st_size / (1024 * 1024)  # MB
                        if file_size <= max_size_mb and file_size > 0:
                            logger.info(f"FFmpeg success: {file_size:.2f} MB")
                            return str(output_file)
                        else:
                            logger.warning(f"File size issue: {file_size:.2f} MB")
                            if output_file.exists():
                                output_file.unlink()
                            return None
                    else:
                        logger.error("FFmpeg completed but no output file created")
                        return None
                else:
                    logger.error(f"FFmpeg failed with code {result.returncode}")
                    logger.error(f"FFmpeg stderr: {result.stderr}")
                    if output_file.exists():
                        output_file.unlink()
                    return None
                    
            except subprocess.TimeoutExpired:
                logger.error("FFmpeg timeout after 5 minutes")
                if output_file.exists():
                    output_file.unlink()
                return None
            except Exception as e:
                logger.error(f"FFmpeg execution error: {e}")
                if output_file.exists():
                    output_file.unlink()
                return None
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, _execute)
    
    async def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """Get video information using FFprobe (part of FFmpeg)"""
        try:
            ffprobe_path = self.ffmpeg_path.replace('ffmpeg.exe', 'ffprobe.exe')
            
            cmd = [
                ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                url
            ]
            
            def _get_info():
                try:
                    result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True, 
                        check=True,
                        timeout=30
                    )
                    return json.loads(result.stdout)
                except Exception as e:
                    logger.error(f"FFprobe failed: {e}")
                    return None
            
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, _get_info)
            
            if info and 'format' in info:
                format_info = info['format']
                duration = float(format_info.get('duration', 0))
                
                return {
                    'title': format_info.get('tags', {}).get('title', 'Unknown'),
                    'duration': int(duration),
                    'uploader': format_info.get('tags', {}).get('artist', 'Unknown'),
                    'view_count': 0,  # FFprobe can't get view count
                    'id': f"ffmpeg_{hash(url) % 100000}",
                    'platform': self._detect_platform(url),
                    'format_name': format_info.get('format_name', ''),
                    'size': int(format_info.get('size', 0))
                }
                
        except Exception as e:
            logger.error(f"Failed to get video info with FFprobe: {e}")
        
        return None
    
    def cleanup_old_files(self, max_age_hours: int = 24):
        """Clean up old downloaded files"""
        import time
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        cleaned = 0
        for file_path in self.download_dir.glob("video_*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    cleaned += 1
                except Exception as e:
                    logger.warning(f"Failed to clean up {file_path}: {e}")
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} old video files")


# Convenience function for easy integration
async def download_video_pure_ffmpeg(url: str, max_size_mb: int = 50, download_dir: str = "downloads") -> Optional[str]:
    """
    Download video using pure FFmpeg - no Python libraries needed
    This is the cleanest, most reliable approach
    """
    service = PureFFmpegVideoService(download_dir=download_dir)
    return await service.download_video(url, max_size_mb)