import os
import time
import subprocess
import sys
from datetime import datetime

def main():
    print("🎬 YouTube Cookie Refresher - Simple Mode")
    print("=========================================")
    print("This will refresh cookies every 2 hours.")
    print("Press Ctrl+C to stop.\n")
    
    while True:
        try:
            print(f"\n🕒 [{datetime.now().strftime('%H:%M:%S')}] Starting cookie refresh...")
            
            # Run the refresher
            result = subprocess.run([
                sys.executable, "cookie_refresher.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Refresh completed successfully")
            else:
                print(f"❌ Refresh failed: {result.stderr}")
            
            print(f"⏰ Waiting 2 hours until next refresh...")
            
            # Wait 2 hours (7200 seconds)
            for i in range(7200):
                time.sleep(1)
                # Check for keyboard interrupt every second
                
        except KeyboardInterrupt:
            print("\n🛑 Stopped by user")
            break
        except Exception as e:
            print(f"💥 Error: {e}")
            print("🔄 Restarting in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    main()