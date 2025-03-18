# Youtube_video_downloader
A simple and user-friendly YouTube Video Downloader with a GUI built using Custom-Tkinter and Yt-dlp
# YouTube Video Downloader GUI Application

![Python](https://img.shields.io/badge/Python-3.7%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)

A modern GUI application for downloading YouTube videos and playlists, built with Python and customtkinter.

## Features

- 📥 Download single videos or entire playlists
- 🎨 Modern dark-mode GUI
- 🎵 Audio-only download option
- 🖼️ Video thumbnail preview
- 📏 Multiple resolution options (144p to 1080p)
- 📁 Choose download directory
- 📊 Real-time progress tracking
- 🌐 Cross-platform support (Windows, macOS, Linux)

## Requirements

- Python 3.7 or higher
- Tcl/Tk (usually included with Python)
- Internet connection

## Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/youtube-downloader.git
```

2. **Create and activate virtual environment(optional)**
```python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```
3. **Install dependencies**
```
pip install -r requirements.txt
```
## Usage
**Application workflow:**

- Enter YouTube URL (video or playlist)
- Click "Fetch Details" to see video information
- Select download options:
    - Audio only checkbox
    - Video resolution
- Click "Download" and choose save location
- View real-time progress in the progress bar
