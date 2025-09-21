#!/usr/bin/env python3
"""
Cookie Setup Guide for Enhanced Video Download

This script helps you set up browser cookies for better video download success rates,
especially for YouTube which has become more restrictive.

IMPORTANT: You need to export your browser cookies to a file named "cookies.txt"
in the project root directory.

Methods to get cookies.txt:

1. BROWSER EXTENSION (Recommended):
   - Chrome: Install "Get cookies.txt LOCALLY" extension
   - Firefox: Install "cookies.txt" extension
   - Visit YouTube while logged in
   - Click the extension and export cookies for youtube.com
   - Save as "cookies.txt" in this project directory

2. MANUAL EXTRACTION:
   - Open browser developer tools (F12)
   - Go to youtube.com while logged in
   - Go to Application/Storage tab > Cookies > https://youtube.com
   - Copy all cookies to a text file in Netscape cookie format

3. AUTOMATIC (if supported):
   - The bot will try to automatically use browser cookies
   - This may not work on all systems

COOKIES.TXT FORMAT:
The file should look like this:
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	FALSE	1234567890	cookie_name	cookie_value
...

SECURITY NOTE:
- Never share your cookies.txt file
- Add cookies.txt to .gitignore
- Regenerate cookies periodically for security
"""

import os
from pathlib import Path

def check_cookies_setup():
    """Check if cookies.txt is properly set up"""
    cookies_file = Path("cookies.txt")
    
    print("🍪 Cookie Setup Checker")
    print("=" * 40)
    
    if cookies_file.exists():
        print("✅ cookies.txt file found!")
        
        # Check file size
        file_size = cookies_file.stat().st_size
        if file_size > 100:  # Should be at least 100 bytes
            print(f"✅ File size looks good: {file_size} bytes")
        else:
            print(f"⚠️  File seems small: {file_size} bytes - make sure it contains actual cookies")
        
        # Check content
        try:
            with open(cookies_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'youtube.com' in content:
                    print("✅ YouTube cookies found in file")
                else:
                    print("⚠️  No YouTube cookies found - make sure to export YouTube cookies")
                
                if content.startswith('# Netscape HTTP Cookie File'):
                    print("✅ Proper Netscape cookie format detected")
                elif '.youtube.com' in content:
                    print("✅ YouTube domain cookies found (format may vary)")
                else:
                    print("⚠️  Cookie format unclear - ensure proper format")
                    
        except Exception as e:
            print(f"❌ Error reading cookies file: {e}")
    
    else:
        print("❌ cookies.txt file not found!")
        print("\n📋 Setup Instructions:")
        print("1. Install a browser extension to export cookies:")
        print("   - Chrome: 'Get cookies.txt LOCALLY'")
        print("   - Firefox: 'cookies.txt'")
        print("2. Visit YouTube while logged in")
        print("3. Export cookies for youtube.com")
        print("4. Save as 'cookies.txt' in this directory")
        print(f"   Directory: {Path.cwd()}")
    
    print("\n" + "=" * 40)
    
    # Check .gitignore
    gitignore_file = Path(".gitignore")
    if gitignore_file.exists():
        try:
            with open(gitignore_file, 'r') as f:
                gitignore_content = f.read()
                if 'cookies.txt' in gitignore_content:
                    print("✅ cookies.txt is in .gitignore (secure)")
                else:
                    print("⚠️  Consider adding 'cookies.txt' to .gitignore for security")
        except:
            pass
    else:
        print("⚠️  No .gitignore found - consider creating one and adding 'cookies.txt'")

def create_gitignore_entry():
    """Add cookies.txt to .gitignore if needed"""
    gitignore_file = Path(".gitignore")
    
    try:
        if gitignore_file.exists():
            with open(gitignore_file, 'r') as f:
                content = f.read()
                if 'cookies.txt' not in content:
                    with open(gitignore_file, 'a') as f:
                        f.write('\n# Browser cookies for video download\ncookies.txt\n')
                    print("✅ Added cookies.txt to .gitignore")
        else:
            with open(gitignore_file, 'w') as f:
                f.write('# Browser cookies for video download\ncookies.txt\n')
            print("✅ Created .gitignore with cookies.txt entry")
    except Exception as e:
        print(f"⚠️  Could not update .gitignore: {e}")

if __name__ == "__main__":
    print(__doc__)
    print("\n" + "=" * 80 + "\n")
    
    check_cookies_setup()
    create_gitignore_entry()
    
    print("\n🎯 Next Steps:")
    print("1. Set up cookies.txt if not already done")
    print("2. Ensure FFmpeg is installed and in PATH")
    print("3. Run: pip install -r requirements.txt")
    print("4. Run: python bot.py")
    print("\n💡 The bot will work without cookies but may have limited success with YouTube")