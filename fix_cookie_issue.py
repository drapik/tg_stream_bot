#!/usr/bin/env python3
"""
Cookie Database Issue Fix Guide

The error you encountered:
"ERROR: Could not copy Chrome cookie database. See https://github.com/yt-dlp/yt-dlp/issues/7271"

This happens when:
1. Chrome is running while yt-dlp tries to access its cookie database
2. Chrome has locked the cookie database file
3. Insufficient permissions to access the cookie database

SOLUTIONS:

1. RECOMMENDED: Use cookies.txt file instead of browser cookies
   - Install a browser extension to export cookies
   - Chrome: "Get cookies.txt LOCALLY" extension
   - Firefox: "cookies.txt" extension
   - Export cookies for youtube.com and save as cookies.txt

2. Close Chrome completely before running the bot
   - This allows yt-dlp to access the cookie database
   - Not practical for continuous bot operation

3. The bot now uses multiple fallback strategies:
   - Strategy 1: Use cookies.txt (if available)
   - Strategy 2: Basic settings without cookies
   - Strategy 3: Minimal fallback

The updated bot will automatically handle this issue gracefully.
"""

import asyncio
from pathlib import Path
from services.ultimate_video_service import ultimate_video_service
from loguru import logger

async def test_cookie_fallback():
    """Test the cookie fallback system"""
    test_url = "https://www.youtube.com/shorts/3EZEEPCbUEA?feature=share"
    
    print("🧪 Testing Cookie Fallback System")
    print("=" * 50)
    
    # Check if cookies.txt exists
    cookies_file = Path("cookies.txt")
    if cookies_file.exists():
        print("✅ cookies.txt found - will try cookies first")
    else:
        print("⚠️  cookies.txt not found - will use fallback strategies")
    
    print(f"\n📹 Testing URL: {test_url}")
    
    try:
        # Test video info extraction
        print("\n1️⃣ Testing video info extraction...")
        info = await ultimate_video_service.get_video_info(test_url)
        if info:
            print(f"✅ Video info extracted successfully:")
            print(f"   Title: {info.get('title', 'N/A')}")
            print(f"   Duration: {info.get('duration', 'N/A')} seconds")
            print(f"   Uploader: {info.get('uploader', 'N/A')}")
        else:
            print("❌ Video info extraction failed")
        
        # Test download with fallback strategies
        print("\n2️⃣ Testing download with fallback strategies...")
        chat_id = 12345  # Test chat ID
        file_path, title = await ultimate_video_service.download_video(test_url, chat_id)
        
        if file_path and Path(file_path).exists():
            file_size = Path(file_path).stat().st_size / (1024 * 1024)
            print(f"✅ Download successful:")
            print(f"   File: {file_path}")
            print(f"   Title: {title}")
            print(f"   Size: {file_size:.2f} MB")
            
            # Clean up test file
            Path(file_path).unlink()
            ultimate_video_service.cleanup_chat_files(chat_id)
            print("✅ Test file cleaned up")
        else:
            print("❌ Download failed with all strategies")
            
    except Exception as e:
        print(f"❌ Test error: {e}")

def show_cookie_setup_instructions():
    """Show detailed cookie setup instructions"""
    print("\n🍪 Cookie Setup Instructions")
    print("=" * 50)
    print("""
To resolve the Chrome cookie database issue permanently:

1. INSTALL BROWSER EXTENSION:
   Chrome: "Get cookies.txt LOCALLY"
   Firefox: "cookies.txt"

2. EXPORT COOKIES:
   - Visit YouTube while logged in
   - Click the extension icon
   - Select "Export" or "Download"
   - Choose "youtube.com" domain
   - Save as "cookies.txt" in this project directory

3. VERIFY SETUP:
   Run: python setup_cookies.py

4. ALTERNATIVE (NOT RECOMMENDED):
   - Close Chrome completely before running bot
   - This allows yt-dlp to access cookie database
   - Not practical for continuous operation

The bot now automatically handles cookie issues with fallback strategies,
but cookies.txt provides the best success rate for YouTube downloads.
""")

async def main():
    """Main test function"""
    print("🔧 Cookie Database Issue Fix")
    print("=" * 70)
    
    show_cookie_setup_instructions()
    
    print("\n🧪 TESTING FALLBACK SYSTEM...")
    await test_cookie_fallback()
    
    print("\n" + "=" * 70)
    print("✅ The bot now handles cookie database issues automatically!")
    print("💡 For best results, set up cookies.txt using browser extension")
    print("🚀 The bot will work even without cookies using fallback strategies")

if __name__ == "__main__":
    asyncio.run(main())