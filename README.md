# YTDownloadX

A Flask web app to download YouTube videos or playlists as MP4 or MP3 using yt-dlp, with QR codes for easy link sharing and optional bundled FFmpeg for Windows.

## Features
- Playlist and single video downloads
- MP4 (video) and MP3 (audio) outputs
- Resolution selection
- Background job with live progress polling
- QR code for download links (handy for mobile)
- Bundled FFmpeg binaries under `resources/ffmpeg/bin` for Windows

## Requirements
- Python 3.11+ (tested with Python 3.13)
- Windows: FFmpeg binaries included under `resources/ffmpeg/bin`
- Other OS: Install FFmpeg and ensure `ffmpeg` and `ffprobe` are on PATH

## Quick Start
1. Create and activate a virtual environment (recommended):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. Run the app:
```powershell
python app.py
```

4. Open the site:
- http://localhost:5000
- The app will also try to show your LAN IP in logs for QR accessibility.

## Usage
1. Paste a YouTube video or playlist URL
2. Click “Fetch Details”
3. Choose format (MP4/MP3) and resolution
4. Start download and watch progress
5. When done, click the provided download link or scan the QR code

## FFmpeg Notes
- The app auto-detects FFmpeg from `resources/ffmpeg/bin` (Windows) or `PATH`
- If FFmpeg is not found, MP4 merges/transcodes may be limited; the app will try single-file formats

## Project Structure
```
app.py                 # Flask app and API endpoints
templates/             # HTML templates (index.html, about.html)
static/                # CSS, client assets
resources/ffmpeg/bin/  # ffmpeg.exe, ffprobe.exe, ffplay.exe (Windows)
requirements.txt       # Python dependencies
README.md              # This file
```

## Troubleshooting
- Metadata fetch fails:
  - Ensure the URL is public and correct
  - Update yt-dlp: `pip install -U yt-dlp`
- MP4 download fails or corrupt output:
  - Ensure FFmpeg is detected (Windows binaries included; otherwise install system FFmpeg)
- Progress stuck at 0%:
  - Check network connectivity and firewall
- QR code not displayed:
  - Ensure the job reached completed state; QR appears when download is ready

## Legal
This project is for personal and educational use only. Respect YouTube’s Terms of Service and copyright laws. Do not download content you do not have rights to.
