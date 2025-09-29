#!/usr/bin/env python3
"""
Automatic YouTube Cookie Refresher for Windows - Simplified
"""

import os
import time
import subprocess
import logging
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cookie_refresh.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class SimpleCookieRefresher:
    def __init__(self):
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        self.cookie_file = os.path.join(self.project_root, 'cookies.txt')
        
    def refresh_cookies(self):
        """Refresh YouTube cookies using available browsers"""
        try:
            logger.info("🚀 Starting cookie refresh...")
            
            # Try different browsers
            browsers = ['chrome', 'firefox', 'edge', 'brave', 'opera']
            
            for browser in browsers:
                try:
                    logger.info(f"🔍 Trying {browser}...")
                    
                    cmd = [
                        sys.executable, '-m', 'yt_dlp',
                        '--cookies-from-browser', browser,
                        '--cookies', self.cookie_file,
                        '--skip-download',
                        '--no-warnings',
                        'https://www.youtube.com'
                    ]
                    
                    # Run with timeout
                    result = subprocess.run(
                        cmd, 
                        capture_output=True, 
                        text=True, 
                        timeout=60,
                        encoding='utf-8'
                    )
                    
                    if result.returncode == 0:
                        if os.path.exists(self.cookie_file) and os.path.getsize(self.cookie_file) > 100:
                            stat = os.stat(self.cookie_file)
                            mod_time = datetime.fromtimestamp(stat.st_mtime)
                            
                            logger.info(f"✅ Success! Cookies updated via {browser} at {mod_time}")
                            return True
                    else:
                        logger.debug(f"{browser} failed: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    logger.warning(f"⏰ {browser} timed out")
                except Exception as e:
                    logger.debug(f"{browser} error: {e}")
            
            logger.error("❌ All browsers failed")
            return False
            
        except Exception as e:
            logger.error(f"💥 Refresh failed: {e}")
            return False

def main():
    """Single refresh run"""
    print("🔄 Running one-time cookie refresh...")
    refresher = SimpleCookieRefresher()
    
    if refresher.refresh_cookies():
        print("✅ Cookie refresh successful!")
        print(f"📁 Cookies saved to: {refresher.cookie_file}")
    else:
        print("❌ Cookie refresh failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()