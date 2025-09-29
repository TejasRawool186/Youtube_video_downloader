"""
Improved YouTube downloader Flask app with playlist support and QR codes.
"""

import os
import io
import uuid
import time
import base64
import socket
import shutil
import threading
import urllib.parse
from typing import Any, Dict, List, Optional
from glob import glob
from datetime import datetime

from flask import Flask, request, jsonify, send_file, send_from_directory, render_template
import yt_dlp
import qrcode
import logging
import zipfile
import subprocess
import tempfile

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory job store and lock
jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()

# Preferred server-side download root (kept outside project dir). Per-job subfolders will be created here.
DOWNLOAD_ROOT = os.path.join(os.path.abspath(os.path.expanduser(os.getenv("YT_DOWNLOAD_ROOT", "/tmp/yt_web"))))
os.makedirs(DOWNLOAD_ROOT, exist_ok=True)

# Detect ffmpeg/ffprobe location so yt_dlp can use it even if PATH isn't loaded
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RES_FFMPEG_BIN = os.path.join(PROJECT_ROOT, "resources", "ffmpeg", "bin")
FFMPEG_DIR = RES_FFMPEG_BIN if os.path.isdir(RES_FFMPEG_BIN) else None
if not FFMPEG_DIR:
    FFMPEG_PATH = shutil.which("ffmpeg")
    FFMPEG_DIR = os.path.dirname(FFMPEG_PATH) if FFMPEG_PATH else None

# ----------------------------
# Enhanced Cookies support
# ----------------------------
COOKIEFILE: Optional[str] = None

def ensure_cookiefile() -> Optional[str]:
    """
    Ensure we have a cookies.txt file available for yt-dlp.
    Priority:
      1) YOUTUBE_COOKIES_FILE (path to file)
      2) cookies.txt in app directory
      3) YOUTUBE_COOKIES (env var containing the cookies.txt contents)
      4) cookies.txt in current working directory
    """
    global COOKIEFILE
    if COOKIEFILE and os.path.isfile(COOKIEFILE):
        return COOKIEFILE

    try:
        logger.info("Looking for YouTube cookies...")
        
        # 1) explicit file path from environment
        env_file = os.getenv('YOUTUBE_COOKIES_FILE')
        if env_file and os.path.isfile(env_file):
            COOKIEFILE = env_file
            logger.info(f"✓ Using YouTube cookie file from YOUTUBE_COOKIES_FILE: {COOKIEFILE}")
            return COOKIEFILE

        # 2) cookies.txt in app directory
        app_cookie_path = os.path.join(PROJECT_ROOT, 'cookies.txt')
        if os.path.isfile(app_cookie_path):
            COOKIEFILE = app_cookie_path
            logger.info(f"✓ Using YouTube cookie file from app directory: {COOKIEFILE}")
            return COOKIEFILE

        # 3) cookie content in env var
        cookies_content = os.getenv('YOUTUBE_COOKIES')
        if cookies_content:
            candidate = os.path.join(PROJECT_ROOT, 'cookies.txt')
            try:
                # Write cookies to file
                with open(candidate, 'w', encoding='utf-8') as f:
                    f.write(cookies_content)
                # Set appropriate permissions
                try:
                    os.chmod(candidate, 0o600)
                except Exception:
                    pass
                COOKIEFILE = candidate
                logger.info(f"✓ Wrote cookies from YOUTUBE_COOKIES env var to: {candidate}")
                return COOKIEFILE
            except Exception as e:
                logger.error(f"✗ Failed to write cookies file from YOUTUBE_COOKIES: {e}")

        # 4) cookies.txt in current working directory
        cwd_cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
        if os.path.isfile(cwd_cookie_path):
            COOKIEFILE = cwd_cookie_path
            logger.info(f"✓ Using YouTube cookie file from current directory: {COOKIEFILE}")
            return COOKIEFILE

        logger.warning("✗ No YouTube cookies configured. Age-restricted videos will not be accessible.")
        return None
        
    except Exception as e:
        logger.exception(f"ensure_cookiefile error: {e}")
        return None

# ----------------------------
# Helper functions (unchanged)
# ----------------------------

def generate_qr_code(url):
    """Generate QR code as base64 data URL"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        logger.error(f"Failed to generate QR code: {e}")
        return None

def resolve_base_url() -> str:
    """Get the base URL for downloads, preferring LAN IP for QR codes"""
    from flask import has_request_context
    
    try:
        if has_request_context():
            host = request.host.split(":")[0]
            port = request.host.split(":")[1] if ":" in request.host else "5000"
            scheme = "https" if request.is_secure else "http"
            
            if host in ("127.0.0.1", "localhost"):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(("8.8.8.8", 80))
                    ip = s.getsockname()[0]
                    s.close()
                    return f"{scheme}://{ip}:{port}/"
                except Exception:
                    pass
            
            return request.host_url
        else:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return f"http://{ip}:5000/"
            except Exception:
                return "http://localhost:5000/"
    except Exception:
        return "http://localhost:5000/"

def get_format_selector(kind: str, resolution: Optional[str]) -> str:
    """Get yt-dlp format selector string"""
    if kind == "mp3":
        return "bestaudio[ext=m4a]/bestaudio[ext=aac]/bestaudio[ext=mp3]/bestaudio/best"
    
    max_h = None
    if resolution:
        digits = "".join(ch for ch in resolution if ch.isdigit())
        max_h = digits if digits else None
    
    if max_h:
        return (
            f"bestvideo[height<={max_h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={max_h}][ext=mp4]+bestaudio[ext=aac]/"
            f"bestvideo[height<={max_h}][ext=webm]+bestaudio[ext=webm]/bestvideo[height<={max_h}][ext=webm]+bestaudio[ext=opus]/"
            f"bestvideo[height<={max_h}]+bestaudio/best[height<={max_h}][ext=mp4]/best[height<={max_h}]/"
            f"bestvideo[height<={max_h}][ext=mp4]+bestaudio/bestvideo[height<={max_h}][ext=webm]+bestaudio/"
            f"bestvideo[height<={max_h}]+bestaudio[ext=m4a]/bestvideo[height<={max_h}]+bestaudio[ext=aac]/"
            f"worst[height<={max_h}]/worst"
        )
    
    return (
        f"bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=aac]/"
        f"bestvideo[ext=webm]+bestaudio[ext=webm]/bestvideo[ext=webm]+bestaudio[ext=opus]/"
        f"bestvideo+bestaudio/best[ext=mp4]/best/"
        f"bestvideo[ext=mp4]+bestaudio/bestvideo[ext=webm]+bestaudio/"
        f"bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio[ext=aac]/"
        f"worst[ext=mp4]/worst"
    )

def progress_hook(d, job_id):
    """Progress hook for yt-dlp downloads"""
    with jobs_lock:
        if job_id not in jobs:
            return
        
        job = jobs[job_id]
        status = d.get('status')
        info = d.get('info_dict') or {}
        pl_index = info.get('playlist_index')
        title = info.get('title')
        filename = d.get('filename')
        
        if 'items' not in job:
            job['items'] = {}
        if pl_index is not None:
            item = job['items'].setdefault(int(pl_index), {'title': title, 'progress': 0, 'status': 'queued', 'filename': None})
            if title and not item.get('title'):
                item['title'] = title
            if filename:
                item['filename'] = os.path.basename(filename)
        
        if status == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate')
            if total and total > 0:
                percentage = (downloaded / total)
                job['progress'] = round(percentage * 100, 2)
            else:
                job['progress'] = None
            job['status'] = 'downloading'
            job['eta'] = d.get('eta')
            job['speed'] = d.get('speed')
            if filename:
                job['filename'] = os.path.basename(filename)
            if pl_index is not None:
                job['items'][int(pl_index)]['progress'] = round((d.get('downloaded_bytes', 0) / (total or 1)) * 100, 1) if total else None
                job['items'][int(pl_index)]['status'] = 'downloading'
        elif status == 'finished':
            job['progress'] = 100
            job['status'] = 'processing'
            if filename:
                job['produced_file'] = filename
            if pl_index is not None:
                job['items'][int(pl_index)]['progress'] = 100
                job['items'][int(pl_index)]['status'] = 'processing'
        elif status == 'postprocessing':
            if filename:
                job['final_file'] = os.path.basename(filename)
                job['status'] = 'processing'
            if pl_index is not None:
                job['items'][int(pl_index)]['status'] = 'processing'

def ffmpeg_bin(name: str) -> Optional[str]:
    """Resolve ffmpeg/ffprobe binaries."""
    if FFMPEG_DIR:
        candidate = os.path.join(FFMPEG_DIR, f"{name}.exe") if os.name == 'nt' else os.path.join(FFMPEG_DIR, name)
        if os.path.isfile(candidate):
            return candidate
    return shutil.which(name)

def sanitize_filename(filename):
    """Remove or replace problematic characters from filenames"""
    import re
    invalid_chars = '<>:"/\\|?*#!'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    filename = re.sub(r'[^\w\s\-_\.\(\)\[\]]', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    filename = filename.strip('_.')
    if not filename:
        filename = 'video'
    if len(filename) > 200:
        filename = filename[:200]
    return filename

def transcode_to_mp4(input_path: str, output_path: str) -> bool:
    """Transcode or remux an input file to MP4 with H.264 video and AAC audio."""
    try:
        ffmpeg = ffmpeg_bin('ffmpeg')
        if not ffmpeg:
            logger.error("FFmpeg not available for transcoding")
            return False
        
        if not os.path.isfile(input_path) or os.path.getsize(input_path) == 0:
            logger.error(f"Input file does not exist or is empty: {input_path}")
            return False
        
        has_video = True
        has_audio = True
            
        ffprobe = ffmpeg_bin('ffprobe')
        if ffprobe:
            probe_cmd = [
                ffprobe, '-v', 'quiet', '-print_format', 'json', '-show_streams', input_path
            ]
            probe_proc = subprocess.run(probe_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8', errors='ignore')
            
            if probe_proc.returncode == 0:
                import json
                try:
                    probe_data = json.loads(probe_proc.stdout)
                    streams = probe_data.get('streams', [])
                    has_video = any(s.get('codec_type') == 'video' for s in streams)
                    has_audio = any(s.get('codec_type') == 'audio' for s in streams)
                    
                    if not has_video:
                        logger.error(f"Input file does not contain video stream: {input_path}")
                        return False
                        
                    video_codec = next((s.get('codec_name') for s in streams if s.get('codec_type') == 'video'), None)
                    audio_codec = next((s.get('codec_name') for s in streams if s.get('codec_type') == 'audio'), None)
                    
                    if video_codec == 'h264' and audio_codec == 'aac' and input_path.lower().endswith('.mp4'):
                        shutil.copy2(input_path, output_path)
                        return True
                        
                except json.JSONDecodeError:
                    pass
        
        if has_audio:
            cmd = [ffmpeg, '-y', '-i', input_path, 
                   '-c:v', 'libx264', '-pix_fmt', 'yuv420p', 
                   '-preset', 'faster', '-crf', '23',
                   '-movflags', '+faststart', 
                   '-c:a', 'aac', '-b:a', '128k', 
                   '-avoid_negative_ts', 'make_zero',
                   output_path]
        else:
            cmd = [ffmpeg, '-y', '-i', input_path, 
                   '-c:v', 'libx264', '-pix_fmt', 'yuv420p', 
                   '-preset', 'faster', '-crf', '23',
                   '-movflags', '+faststart', '-an',
                   '-avoid_negative_ts', 'make_zero',
                   output_path]
        
        logger.info(f"Transcoding to MP4: {' '.join(cmd)}")
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='utf-8', errors='ignore')
            
        if proc.returncode == 0 and os.path.isfile(output_path) and os.path.getsize(output_path) > 0:
            return True
        stderr_output = proc.stderr or ""
        logger.error(f"Transcode failed rc={proc.returncode}: {stderr_output[:500]}")
        return False
    except Exception as e:
        logger.exception(f"Exception during MP4 transcode: {e}")
        return False

def download_worker(job_id, url, kind, resolution, selection_ids):
    """Worker function for downloading videos with per-job directory"""
    try:
        with jobs_lock:
            if job_id not in jobs:
                return
            jobs[job_id]['status'] = 'starting'
            jobs[job_id]['current_video'] = 1
            jobs[job_id]['total_videos'] = len(selection_ids) if selection_ids else 1
            jobs[job_id]['items'] = {}
            jobs[job_id]['is_playlist'] = True if selection_ids else False
        
        # Create per-job directory
        job_dir = os.path.join(DOWNLOAD_ROOT, job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Configure yt-dlp options
        format_selector = get_format_selector(kind, resolution)
        
        ydl_opts = {
            'format': format_selector,
            'outtmpl': os.path.join(job_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: progress_hook(d, job_id)],
            'ignoreerrors': True,
            'prefer_ffmpeg': True,
            'prefer_free_formats': False,
            'continuedl': True,
            'concurrent_fragment_downloads': 4,
            'fragment_retries': 10,
            'retries': 10,
            'socket_timeout': 60,
            'http_chunk_size': 1048576,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'noplaylist': False,
            'writesubtitles': False,
            'writethumbnail': False,
            'writeinfojson': False,
            'keepvideo': False,
            'fixup': 'detect_or_warn',
            'prefer_insecure': False,
            'geo_bypass': True,
            'sleep_interval': 0,
            'max_sleep_interval': 1,
            'sleep_interval_subtitles': 0,
        }

        # Attach cookiefile if available
        cookiefile = ensure_cookiefile()
        if cookiefile:
            ydl_opts['cookiefile'] = cookiefile
            logger.info(f"Using cookie file for job {job_id}: {cookiefile}")
        
        # For video downloads, ensure proper merging and MP4 output
        if kind == "mp4":
            if FFMPEG_DIR or shutil.which('ffmpeg'):
                ydl_opts['merge_output_format'] = 'mp4'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': 'mp4'
                }]
                ydl_opts['postprocessor_args'] = {
                    'ffmpeg': ['-movflags', '+faststart']
                }
            else:
                logger.warning("FFmpeg not available - using single-file formats")
                format_selector = (
                    f"best[ext=mp4]/best[ext=webm]/best/"
                    f"worst[ext=mp4]/worst[ext=webm]/worst"
                )
                ydl_opts['format'] = format_selector
        
        if kind == "mp3":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        # Explicit FFmpeg configuration
        ffmpeg_path = ffmpeg_bin('ffmpeg')
        ffprobe_path = ffmpeg_bin('ffprobe')
        
        if ffmpeg_path and ffprobe_path:
            ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_path)
            if FFMPEG_DIR:
                ydl_opts['ffmpeg_location'] = FFMPEG_DIR
            logger.info(f"Using FFmpeg from: {os.path.dirname(ffmpeg_path)}")
        
        # Handle playlist selection
        if selection_ids:
            try:
                indices = [int(x) for x in selection_ids]
                ydl_opts['playlist_items'] = ','.join(str(i) for i in indices)
                logger.info(f"Playlist items selected: {ydl_opts['playlist_items']}")
            except Exception as e:
                logger.error(f"Invalid selection IDs: {e}")
                pass
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            with jobs_lock:
                jobs[job_id]['status'] = 'downloading'
            ydl.download([url])
        
        # After download, collect produced files
        files = sorted(glob(os.path.join(job_dir, "**"), recursive=True))
        
        def is_final_file(path: str) -> bool:
            name = os.path.basename(path).lower()
            if not os.path.isfile(path) or os.path.getsize(path) == 0:
                return False
            if name.endswith(('.part', '.ytdl', '.tmp', '.temp', '.f4v', '.f4a')):
                return False
            if '.part.' in name or '.ytdl.' in name or '.tmp.' in name or '.temp.' in name:
                return False
            if name.endswith(('.jpg', '.jpeg', '.png', '.webp', '.json', '.vtt', '.srt', '.txt', '.info')):
                return False
            return name.endswith((".mp4", ".mp3", ".m4a", ".webm", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".3gp"))
        
        downloaded_files = [p for p in files if is_final_file(p)]
        
        def has_proper_video_stream(path: str) -> bool:
            """Check if file contains proper video stream"""
            try:
                ffprobe = ffmpeg_bin('ffprobe')
                if not ffprobe:
                    return True
                
                cmd = [ffprobe, '-v', 'quiet', '-print_format', 'json', '-show_streams', path]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=15, encoding='utf-8', errors='ignore')
                
                if proc.returncode != 0:
                    return True
                
                import json
                try:
                    data = json.loads(proc.stdout)
                    streams = data.get('streams', [])
                    video_streams = [s for s in streams if s.get('codec_type') == 'video']
                    if not video_streams:
                        return False
                    video_stream = video_streams[0]
                    width = video_stream.get('width', 0)
                    height = video_stream.get('height', 0)
                    return width > 0 and height > 0
                except json.JSONDecodeError:
                    return True
            except Exception as e:
                logger.warning(f"Error checking video stream in {path}: {e}")
                return True
        
        def validate_file_integrity(path: str) -> bool:
            """Validate file integrity using ffprobe"""
            try:
                if not os.path.isfile(path) or os.path.getsize(path) == 0:
                    return False
                ffprobe = ffmpeg_bin('ffprobe')
                if not ffprobe:
                    return True
                cmd = [ffprobe, '-v', 'quiet', '-print_format', 'json', '-show_format', path]
                proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10, encoding='utf-8', errors='ignore')
                return proc.returncode == 0
            except Exception as e:
                logger.warning(f"Error validating file {path}: {e}")
                return True
        
        # Validate files
        if kind == 'mp4':
            valid_files = []
            for p in downloaded_files:
                if has_proper_video_stream(p) and validate_file_integrity(p):
                    valid_files.append(p)
                else:
                    logger.warning(f"File {p} failed validation")
            downloaded_files = valid_files
        elif kind == 'mp3':
            valid_files = []
            for p in downloaded_files:
                if validate_file_integrity(p):
                    valid_files.append(p)
                else:
                    logger.warning(f"Audio file {p} failed validation")
            downloaded_files = valid_files
        
        # Determine if this is a playlist
        with jobs_lock:
            detected_indices = list((jobs[job_id].get('items') or {}).keys())
            is_playlist = len(detected_indices) > 1 or len(downloaded_files) > 1
            jobs[job_id]['is_playlist'] = is_playlist
        
        if not downloaded_files:
            logger.error(f"No suitable final files for job {job_id}")
            raise Exception("No video files were downloaded successfully.")
        
        # Resolve base URL
        base_url = resolve_base_url()
        with jobs_lock:
            jobs[job_id]['completed_at'] = datetime.now().isoformat()
        
        if is_playlist and len(downloaded_files) > 1:
            # ZIP for playlist
            zip_name = f"{job_id}.zip"
            zip_path = os.path.join(job_dir, zip_name)
            with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
                for f in downloaded_files:
                    zf.write(f, arcname=os.path.basename(f))
            zip_url = f"{base_url}download/{job_id}/{zip_name}"
            qr_code = generate_qr_code(zip_url)
            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id]['files'] = [os.path.relpath(f, job_dir) for f in downloaded_files]
                    jobs[job_id].update({
                        'status': 'completed',
                        'progress': 100,
                        'filename': zip_name,
                        'final_file': zip_name,
                        'download_url': zip_url,
                        'qr': qr_code,
                    })
        else:
            # Single output file
            best_file = max(downloaded_files, key=lambda p: os.path.getsize(p))
            output_file = best_file
            
            # Ensure MP4 output for video downloads
            if kind == 'mp4' and not best_file.lower().endswith('.mp4'):
                base_name = os.path.splitext(os.path.basename(best_file))[0]
                sanitized_name = sanitize_filename(base_name) + '.mp4'
                mp4_out = os.path.join(job_dir, sanitized_name)
                
                logger.info(f"Transcoding {best_file} to MP4 format")
                try:
                    ok = transcode_to_mp4(best_file, mp4_out)
                    if ok and os.path.isfile(mp4_out) and os.path.getsize(mp4_out) > 0:
                        output_file = mp4_out
                        try:
                            os.remove(best_file)
                        except:
                            pass
                        logger.info(f"Successfully transcoded to: {sanitized_name}")
                    else:
                        logger.warning("Transcode failed, using original file")
                except Exception as e:
                    logger.warning(f"Transcode failed with exception: {e}, using original file")
            
            filename = os.path.basename(output_file)
            download_url = f"{base_url}download/{job_id}/{urllib.parse.quote(filename)}"
            qr_code = generate_qr_code(download_url)
            
            with jobs_lock:
                if job_id in jobs:
                    jobs[job_id].update({
                        'status': 'completed',
                        'progress': 100,
                        'filename': filename,
                        'final_file': filename,
                        'download_url': download_url,
                        'qr': qr_code,
                    })
                    
    except Exception as e:
        logger.exception(f"Download worker error for job {job_id}: {e}")
        with jobs_lock:
            if job_id in jobs:
                jobs[job_id].update({
                    'status': 'error',
                    'error': str(e),
                    'progress': 0,
                })

# ----------------------------
# Enhanced Metadata Extraction with Cookies
# ----------------------------

def extract_metadata_with_cookies(url: str) -> Optional[Dict[str, Any]]:
    """Extract metadata using cookies with multiple fallback strategies"""
    strategies = [
        # Strategy 1: Simple extraction with cookies
        {
            'skip_download': True,
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        },
        # Strategy 2: Flat extraction for playlists
        {
            'skip_download': True,
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
        },
        # Strategy 3: No format preferences
        {
            'skip_download': True,
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
        },
        # Strategy 4: Worst format (more likely available)
        {
            'skip_download': True,
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'format': 'worst',
        },
    ]
    
    cookiefile = ensure_cookiefile()
    
    for i, strategy in enumerate(strategies):
        try:
            strategy_copy = strategy.copy()
            if cookiefile:
                strategy_copy['cookiefile'] = cookiefile
                logger.info(f"Trying metadata extraction strategy {i+1} with cookies")
            else:
                logger.info(f"Trying metadata extraction strategy {i+1} without cookies")
            
            with yt_dlp.YoutubeDL(strategy_copy) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    logger.info(f"✓ Metadata extraction succeeded with strategy {i+1}")
                    return info
        except Exception as e:
            logger.warning(f"✗ Metadata extraction strategy {i+1} failed: {e}")
            continue
    
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/metadata', methods=['POST'])
def get_metadata():
    """Get video/playlist metadata with enhanced cookie support"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        # Validate YouTube URL
        if 'youtube.com' not in url and 'youtu.be' not in url:
            return jsonify({'error': 'Please enter a valid YouTube URL'}), 400
        
        # Check cookies status
        cookiefile = ensure_cookiefile()
        if cookiefile:
            logger.info(f"Using cookies for metadata extraction: {cookiefile}")
        else:
            logger.warning("No cookies available for metadata extraction")
        
        # Extract metadata
        info = extract_metadata_with_cookies(url)
        
        if not info:
            error_msg = "Unable to access this video."
            if cookiefile:
                error_msg += " The video might be unavailable or require different authentication."
            else:
                error_msg += " This video might be age-restricted or private. Cookies are required for access."
            
            return jsonify({'error': error_msg}), 500
        
        # Process playlist or single video
        if info.get('_type') == 'playlist':
            entries = []
            for i, entry in enumerate(info.get('entries', [])):
                if entry:
                    entries.append({
                        'title': entry.get('title', f'Video {i+1}'),
                        'thumbnail': entry.get('thumbnail'),
                        'duration': entry.get('duration'),
                        'resolutions': ['1080p', '720p', '480p', '360p']
                    })
            
            return jsonify({
                'type': 'playlist',
                'title': info.get('title', 'Playlist'),
                'entries': entries
            })
        else:
            # Single video
            title = info.get('title', 'Unknown Video')
            thumbnail = info.get('thumbnail')
            duration = info.get('duration')
            channel = info.get('uploader') or info.get('channel')
            
            # Extract available resolutions
            resolutions = ['1080p', '720p', '480p', '360p']
            try:
                formats = info.get('formats', [])
                available_res = set()
                for fmt in formats:
                    height = fmt.get('height')
                    if height:
                        available_res.add(f"{height}p")
                
                if available_res:
                    resolutions = sorted(list(available_res), key=lambda x: int(x.replace('p', '')), reverse=True)
            except:
                pass
            
            return jsonify({
                'type': 'video',
                'video': {
                    'title': title,
                    'thumbnail': thumbnail,
                    'duration': duration,
                    'channel': channel,
                    'resolutions': resolutions
                }
            })
                
    except Exception as e:
        logger.exception(f"Metadata extraction failed: {e}")
        
        error_msg = str(e).lower()
        if 'private' in error_msg or 'sign in' in error_msg:
            return jsonify({
                'error': 'This video is private or requires login. Private videos require valid YouTube cookies.'
            }), 500
        elif 'unavailable' in error_msg or 'not available' in error_msg:
            return jsonify({
                'error': 'This video is not available in your region or has been removed.'
            }), 500
        elif 'age restricted' in error_msg:
            return jsonify({
                'error': 'This is an age-restricted video. Valid YouTube cookies are required for access.'
            }), 500
        else:
            return jsonify({
                'error': f'Failed to get video information: {str(e)}'
            }), 500

@app.route('/api/download', methods=['POST'])
def start_download():
    """Start a download job"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        kind = data.get('kind', 'mp4')
        resolution = data.get('resolution')
        selection_ids = data.get('selection_ids', [])
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        job_id = str(uuid.uuid4())
        
        with jobs_lock:
            jobs[job_id] = {
                'id': job_id,
                'url': url,
                'kind': kind,
                'resolution': resolution,
                'selection_ids': selection_ids,
                'status': 'queued',
                'progress': 0,
                'created_at': datetime.now().isoformat(),
            }
        
        # Start download in background thread
        thread = threading.Thread(
            target=download_worker,
            args=(job_id, url, kind, resolution, selection_ids),
            daemon=True
        )
        thread.start()
        
        return jsonify({'job_id': job_id})
        
    except Exception as e:
        logger.exception(f"Download start failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/progress/<job_id>')
def get_progress(job_id):
    """Get download progress"""
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        items_dict = job.get('items', {})
        items_list = []
        for idx, item_data in items_dict.items():
            items_list.append({
                'index': idx,
                'title': item_data.get('title', f'Item {idx}'),
                'progress': item_data.get('progress', 0),
                'status': item_data.get('status', 'queued'),
                'filename': item_data.get('filename')
            })
        
        result = {
            'status': job.get('status'),
            'progress': job.get('progress', 0),
            'filename': job.get('filename'),
            'eta': job.get('eta'),
            'speed': job.get('speed'),
            'total_videos': job.get('total_videos', 1),
            'current_video': job.get('current_video', 1),
            'is_playlist': job.get('is_playlist', False),
            'items': items_list,
            'download_url': job.get('download_url'),
            'qr': job.get('qr'),
            'error': job.get('error')
        }
        
        return jsonify(result)

@app.route('/download/<job_id>/<filename>')
def download_file(job_id, filename):
    """Download a file"""
    try:
        job_dir = os.path.join(DOWNLOAD_ROOT, job_id)
        file_path = os.path.join(job_dir, filename)
        
        if not os.path.isfile(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.exception(f"Download file failed: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

if __name__ == '__main__':
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    
    print("Starting YouTube Downloader...")
    print("Access the app at: http://localhost:5000")
    
    # Check for cookies
    cookiefile = ensure_cookiefile()
    if cookiefile:
        print(f"✓ YouTube cookies loaded from: {cookiefile}")
    else:
        print("⚠ No YouTube cookies found. Age-restricted videos will not be accessible.")
    
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)