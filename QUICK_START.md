# 🚀 YTDownloadX - Quick Start Guide

Get YTDownloadX up and running in less than 5 minutes!

---

## ⚡ Super Quick Start (1 minute)

```bash
# Clone and run
git clone https://github.com/TejasRawool186/Youtube_video_downloader.git
cd Youtube_video_downloader
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 in your browser. Done! 🎉

---

## 📋 Prerequisites

Before you begin, ensure you have:

- ✅ **Python 3.11 or higher** ([Download](https://www.python.org/downloads/))
- ✅ **pip** (comes with Python)
- ✅ **Git** ([Download](https://git-scm.com/downloads))
- ✅ **FFmpeg** (included for Windows, auto-installed on others)

### Check Your Setup

```bash
# Check Python version
python --version
# Should show: Python 3.11.x or higher

# Check pip
pip --version
# Should show: pip 23.x or higher

# Check Git
git --version
# Should show: git version 2.x or higher
```

---

## 🎯 Installation Methods

### Method 1: Standard Installation (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ytdownloadx.git
cd ytdownloadx

# 2. Create virtual environment
python -m venv .venv

# 3. Activate virtual environment
# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# Windows (CMD)
.\.venv\Scripts\activate.bat
# Linux/Mac
source .venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the application
python app.py

# 6. Open in browser
# Navigate to: http://localhost:5000
```

### Method 2: Docker (Easiest)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/ytdownloadx.git
cd ytdownloadx

# 2. Build and run with Docker Compose
docker-compose up -d

# 3. Open in browser
# Navigate to: http://localhost:5000
```

### Method 3: One-Line Install (Linux/Mac)

```bash
curl -sSL https://raw.githubusercontent.com/TejasRawool186/Youtube_video_downloader/main/install.sh | bash
```

---

## 🎮 First Use

### Step 1: Open the App

Navigate to http://localhost:5000 in your browser.

### Step 2: Download a Video

1. **Paste a YouTube URL** in the input field
   ```
   Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ
   ```

2. **Click "Fetch Details"**
   - Wait for video information to load
   - Thumbnail and title will appear

3. **Select Format and Quality**
   - Format: MP4 (video) or MP3 (audio)
   - Quality: Choose from available options

4. **Click "Start Download"**
   - Progress bar will show download status
   - File downloads automatically when complete

5. **Scan QR Code (Optional)**
   - QR code appears after download
   - Scan with phone to download on mobile

### Step 3: Download a Playlist

1. **Paste a playlist URL**
   ```
   Example: https://www.youtube.com/playlist?list=PLxxxxxx
   ```

2. **Click "Fetch Details"**
   - All videos in playlist will appear

3. **Select Videos**
   - Check boxes for videos you want
   - Or click "Select All"

4. **Choose Format and Quality**

5. **Click "Download Selected"**
   - Videos download one by one
   - Progress shown for each video

---

## 🔧 Configuration (Optional)

### Basic Configuration

Create a `.env` file in the project root:

```bash
# Copy example configuration
cp .env.example .env

# Edit with your preferred settings
# Windows
notepad .env
# Linux/Mac
nano .env
```

### Essential Settings

```env
# Application
PORT=5000
FLASK_DEBUG=False

# Downloads
DOWNLOAD_TTL=1800  # 30 minutes

# Features
ENABLE_PLAYLISTS=True
ENABLE_QR_CODES=True
ENABLE_NOTIFICATIONS=True
```

---

## 🌐 Deploy to Production

### Deploy to Render.com (Free)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/TejasRawool186/Youtube_video_downloader.git
   git push -u origin main
   ```

2. **Deploy on Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Click "Create Web Service"
   - Wait 5-10 minutes

3. **Access Your App**
   ```
   https://your-app-name.onrender.com
   ```

### Deploy with Docker

```bash
# Build image
docker build -t ytdownloadx .

# Run container
docker run -d -p 5000:5000 --name ytdownloadx ytdownloadx

# Check logs
docker logs ytdownloadx

# Stop container
docker stop ytdownloadx
```

---

## 🐛 Troubleshooting

### Common Issues

#### Issue: "Python not found"

**Solution:**
```bash
# Windows: Add Python to PATH during installation
# Or download from: https://www.python.org/downloads/

# Linux
sudo apt install python3 python3-pip

# Mac
brew install python3
```

#### Issue: "pip install fails"

**Solution:**
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Try again
pip install -r requirements.txt
```

#### Issue: "Port 5000 already in use"

**Solution:**
```bash
# Change port in .env file
PORT=8000

# Or kill process using port 5000
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:5000 | xargs kill -9
```

#### Issue: "Download fails"

**Solution:**
1. Check internet connection
2. Update yt-dlp: `pip install -U yt-dlp`
3. Try a different video
4. Check if video is public

#### Issue: "QR code doesn't work on mobile"

**Solution:**
- QR codes work best with HTTPS
- Deploy to production (Render, Railway, etc.)
- Or use ngrok for local HTTPS testing

---

## 📚 Next Steps

### Learn More

- 📖 [Full Documentation](DOCUMENTATION.md)
- 🤝 [Contributing Guide](CONTRIBUTING.md)
- 🔒 [Security Policy](SECURITY.md)
- 📝 [Changelog](CHANGELOG.md)

### Get Help

- 🐛 [Report a Bug](https://github.com/yourusername/ytdownloadx/issues)
- 💡 [Request a Feature](https://github.com/yourusername/ytdownloadx/issues)
- 📧 [Email Support](mailto:tejasrawool186@gmail.com)

### Watch Demo

- 🎥 [Official Demo Video](https://youtu.be/oyjuRt3NIJU)
- 🌐 [Live Demo](https://ytdownloadx.curiositybytejas.cloud/)

---

## 🎯 Quick Commands Reference

```bash
# Start application
python app.py

# Run tests
python test_app.py

# Update dependencies
pip install -r requirements.txt --upgrade

# Check for security issues
pip install bandit
bandit -r .

# Format code
pip install black
black app.py

# Lint code
pip install flake8
flake8 app.py

# Build Docker image
docker build -t ytdownloadx .

# Run Docker container
docker run -p 5000:5000 ytdownloadx

# View logs
# Local
tail -f ytdownloadx.log

# Docker
docker logs -f ytdownloadx
```

---

## 💡 Pro Tips

### Tip 1: Use Virtual Environment
Always use a virtual environment to avoid dependency conflicts:
```bash
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
.\.venv\Scripts\Activate.ps1  # Windows
```

### Tip 2: Update Regularly
Keep yt-dlp updated for best compatibility:
```bash
pip install -U yt-dlp
```

### Tip 3: Enable Notifications
Enable desktop notifications for download completion:
- Click the 🔔 button in the app
- Allow notifications in your browser

### Tip 4: Use HTTPS in Production
Always deploy with HTTPS for:
- Better security
- Working QR codes on mobile
- Browser trust

### Tip 5: Monitor Disk Space
Downloads are auto-deleted after 30 minutes, but monitor disk space:
```bash
# Check disk space
df -h  # Linux/Mac
wmic logicaldisk get size,freespace,caption  # Windows
```

---

## 🎉 Success!

You're all set! Start downloading YouTube videos with YTDownloadX.

### What's Next?

1. ⭐ **Star the repository** on GitHub
2. 🐛 **Report bugs** if you find any
3. 💡 **Suggest features** you'd like to see
4. 🤝 **Contribute** to the project
5. 📢 **Share** with friends

---

## 📞 Need Help?

- **Documentation:** [DOCUMENTATION.md](DOCUMENTATION.md)
- **Issues:** [GitHub Issues](https://github.com/TejasRawool186/Youtube_video_downloader/issues)
- **Email:** tejasrawool186@gmail.com
- **Live Demo:** https://ytdownloadx.curiositybytejas.cloud/

---

<div align="center">

**Happy Downloading! 🎬**

Made with ❤️ by the YTDownloadX Team

[🌐 Live Demo](https://ytdownloadx.curiositybytejas.cloud/) • [📺 Video Demo](https://youtu.be/oyjuRt3NIJU) • [📖 Documentation](DOCUMENTATION.md)

</div>
