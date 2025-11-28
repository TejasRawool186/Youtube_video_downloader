"""
Simple YouTube downloader Flask app - 360p quality
"""

import os
import io
import uuid
import base64
import socket
import shutil
import threading
import urllib.parse
from typing import Any, Dict, Optional
from glob import glob
from datetime import datetime

from flask import Flask, request, jsonify, send_file, render_template
import yt_dlp
import qrcode
import logging
import zipfile
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# In-memory job store
jobs: Dict[str, Dict[str, Any]] = {}
jobs_lock = threading.Lock()

# Download directory
DOWNLOAD_ROOT = os.path.join(os.path.abspath(os.path.expanduser(os.getenv("YT_DOWNLOAD_ROOT", "/tmp/yt_web"))))
os.makedirs(DOWNLOAD_ROOT, exist_ok=True)

# Detect ffmpeg
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
RES_FFMPEG_BIN = os.path.join(PROJECT_ROOT, "resources", "ffmpeg", "bin")
FFMPEG_DIR = RES_FFMPEG_BIN if os.path.isdir(RES_FFMPEG_BIN) else None
if not FFMPEG_DIR:
    FFMPEG_PATH = shutil.which("ffmpeg")
    FFMPEG_DIR = os.path.dirname(FFMPEG_PATH) if FFMPEG_PATH else None

# ----------------------------
# Helper functions
# ----------------------------

def generate_qr_code(url):
    """Generate QR code as base64 data URL"""
    try:
        qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
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
    """Get the base URL for downloads"""
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

def get_format_selector(kind: str) -> str:
    """Get yt-dlp format selector - 360p for video, best audio for mp3"""
    if kind == "mp3":
        return "bestaudio[ext=m4a]/bestaudio/best"
    # 360p video
    return "best[height<=360][ext=mp4]/best[height<=360]/best[ext=mp4]/best"

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

def ffmpeg_bin(name: str) -> Optional[str]:
    """Resolve ffmpeg/ffprobe binaries"""
    if FFMPEG_DIR:
        candidate = os.path.join(FFMPEG_DIR, f"{name}.exe") if os.name == 'nt' else os.path.join(FFMPEG_DIR, name)
        if os.path.isfile(candidate):
            return candidate
    return shutil.which(name)

def sanitize_filename(filename):
    """Remove problematic characters from filenames"""
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

def download_worker(job_id, url, kind, selection_ids):
    """Worker function for downloading videos"""
    try:
        with jobs_lock:
            if job_id not in jobs:
                return
            jobs[job_id]['status'] = 'starting'
            jobs[job_id]['current_video'] = 1
            jobs[job_id]['total_videos'] = len(selection_ids) if selection_ids else 1
            jobs[job_id]['items'] = {}
            jobs[job_id]['is_playlist'] = True if selection_ids else False
        
        # Create job directory
        job_dir = os.path.join(DOWNLOAD_ROOT, job_id)
        os.makedirs(job_dir, exist_ok=True)
        
        # Configure yt-dlp options
        format_selector = get_format_selector(kind)
        logger.info(f"Job {job_id}: kind={kind}, format={format_selector}")
        
        ydl_opts = {
            'format': format_selector,
            'outtmpl': os.path.join(job_dir, '%(title)s.%(ext)s'),
            'progress_hooks': [lambda d: progress_hook(d, job_id)],
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'noplaylist': False,
        }

        # For video downloads, ensure MP4 output
        if kind == "mp4" and FFMPEG_DIR:
            ydl_opts['merge_output_format'] = 'mp4'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4'
            }]
        
        if kind == "mp3":
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        # FFmpeg configuration
        ffmpeg_path = ffmpeg_bin('ffmpeg')
        if ffmpeg_path:
            ydl_opts['ffmpeg_location'] = os.path.dirname(ffmpeg_path)
        
        # Handle playlist selection
        if selection_ids:
            try:
                indices = [int(x) for x in selection_ids]
                ydl_opts['playlist_items'] = ','.join(str(i) for i in indices)
            except Exception as e:
                logger.error(f"Invalid selection IDs: {e}")
        
        # Download
        with jobs_lock:
            jobs[job_id]['status'] = 'downloading'
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Collect downloaded files
        files = sorted(glob(os.path.join(job_dir, "**"), recursive=True))
        
        def is_final_file(path: str) -> bool:
            name = os.path.basename(path).lower()
            if not os.path.isfile(path) or os.path.getsize(path) == 0:
                return False
            if name.endswith(('.part', '.ytdl', '.tmp', '.temp')):
                return False
            if name.endswith(('.jpg', '.jpeg', '.png', '.json', '.vtt', '.srt', '.txt')):
                return False
            return name.endswith((".mp4", ".mp3", ".m4a", ".webm", ".mkv"))
        
        downloaded_files = [p for p in files if is_final_file(p)]
        
        if not downloaded_files:
            raise Exception("No video files were downloaded successfully.")
        
        # Resolve base URL
        base_url = resolve_base_url()
        with jobs_lock:
            jobs[job_id]['completed_at'] = datetime.now().isoformat()
        
        # Determine if playlist
        with jobs_lock:
            detected_indices = list((jobs[job_id].get('items') or {}).keys())
            is_playlist = len(detected_indices) > 1 or len(downloaded_files) > 1
            jobs[job_id]['is_playlist'] = is_playlist
        
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
            # Single file
            best_file = max(downloaded_files, key=lambda p: os.path.getsize(p))
            filename = os.path.basename(best_file)
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
# Routes
# ----------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/api/metadata', methods=['POST'])
def get_metadata():
    """Get video/playlist metadata"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if 'youtube.com' not in url and 'youtu.be' not in url:
            return jsonify({'error': 'Please enter a valid YouTube URL'}), 400
        
        # Extract metadata
        ydl_opts = {
            'skip_download': True,
            'ignoreerrors': True,
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        
        if not info:
            return jsonify({'error': 'Unable to access this video'}), 400
        
        # Check if playlist
        is_playlist = 'entries' in info
        
        if is_playlist:
            entries = info.get('entries', [])
            videos = []
            # Get common resolutions from all videos
            all_resolutions = set()
            for idx, entry in enumerate(entries, 1):
                if entry:
                    # Extract available formats
                    formats = entry.get('formats', [])
                    for fmt in formats:
                        height = fmt.get('height')
                        if height:
                            all_resolutions.add(f"{height}p")
                    
                    videos.append({
                        'index': idx,
                        'title': entry.get('title', f'Video {idx}'),
                        'duration': entry.get('duration'),
                        'thumbnail': entry.get('thumbnail'),
                        'id': entry.get('id'),
                        'resolutions': sorted(list(all_resolutions), key=lambda x: int(x.replace('p', '')), reverse=True)
                    })
            
            # Standard resolution options for UI
            standard_resolutions = ['2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p']
            
            return jsonify({
                'type': 'playlist',
                'title': info.get('title', 'Playlist'),
                'uploader': info.get('uploader'),
                'video_count': len(videos),
                'videos': videos,
                'entries': videos  # For compatibility
            })
        else:
            # Extract available formats for single video
            formats = info.get('formats', [])
            resolutions = set()
            for fmt in formats:
                height = fmt.get('height')
                if height:
                    resolutions.add(f"{height}p")
            
            # Standard resolution options for UI (even if not all available)
            standard_resolutions = ['2160p', '1440p', '1080p', '720p', '480p', '360p', '240p', '144p']
            
            return jsonify({
                'type': 'video',
                'video': {
                    'title': info.get('title'),
                    'channel': info.get('uploader') or info.get('channel'),
                    'duration': info.get('duration'),
                    'thumbnail': info.get('thumbnail'),
                    'description': info.get('description', '')[:200],
                    'resolutions': standard_resolutions  # Show all options in UI
                }
            })
            
    except Exception as e:
        logger.exception(f"Metadata error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download', methods=['POST'])
def start_download():
    """Start download job - always downloads 360p regardless of user selection"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        kind = data.get('kind', 'mp4')
        resolution = data.get('resolution', '360p')  # Accept but ignore - always use 360p
        selection_ids = data.get('selection', [])
        
        if not url:
            return jsonify({'error': 'URL is required'}), 400
        
        if kind not in ('mp4', 'mp3'):
            return jsonify({'error': 'Invalid format'}), 400
        
        job_id = str(uuid.uuid4())
        
        with jobs_lock:
            jobs[job_id] = {
                'status': 'queued',
                'progress': 0,
                'url': url,
                'kind': kind,
                'requested_resolution': resolution,  # Store what user requested
                'actual_resolution': '360p',  # But always download 360p
                'created_at': datetime.now().isoformat()
            }
        
        # Start download in background (always 360p)
        thread = threading.Thread(target=download_worker, args=(job_id, url, kind, selection_ids))
        thread.daemon = True
        thread.start()
        
        return jsonify({'job_id': job_id})
        
    except Exception as e:
        logger.exception(f"Download start error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def get_status(job_id):
    """Get job status"""
    with jobs_lock:
        job = jobs.get(job_id)
        if not job:
            return jsonify({'error': 'Job not found'}), 404
        
        # Convert items dict to array for frontend
        job_copy = job.copy()
        if 'items' in job_copy and isinstance(job_copy['items'], dict):
            items_array = []
            for idx, item in sorted(job_copy['items'].items()):
                item_copy = item.copy()
                item_copy['index'] = idx
                items_array.append(item_copy)
            job_copy['items'] = items_array
        
        return jsonify(job_copy)

@app.route('/api/progress/<job_id>', methods=['GET'])
def get_progress(job_id):
    """Get job progress (alias for status)"""
    return get_status(job_id)

@app.route('/download/<job_id>/<path:filename>')
def download_file(job_id, filename):
    """Download file"""
    try:
        job_dir = os.path.join(DOWNLOAD_ROOT, job_id)
        file_path = os.path.join(job_dir, filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.exception(f"Download file error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
