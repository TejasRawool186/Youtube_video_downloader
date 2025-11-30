import os
import re
import threading
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_file,
)
import yt_dlp
import logging

# ---------------------------------------------------------
# BASIC SETUP
# ---------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

COOKIES_PATH = BASE_DIR / "cookies.txt"

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ytdownloadx")

# global flag to fall back to simple options if something misbehaves
USE_SIMPLE_VERSION = False

# Files older than this (seconds) will be deleted by the cleanup thread
DOWNLOAD_TTL_SECONDS = 60 * 30  # 30 minutes

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------


def safe_download_name(title: str, ext: str) -> str:
    """
    Build a *HTTP-header-safe* download filename.

    - Removes weird characters (/, ?, :, etc.)
    - Keeps only letters, numbers, spaces, dash, underscore and dot
    - Ensures we always return something ASCII-ish
    """
    if not title:
        base = "video"
    else:
        # Replace disallowed chars with underscore
        base = "".join(
            c if c.isalnum() or c in " .-_"
            else "_"
            for c in title
        )
        # Collapse multiple underscores/spaces
        base = re.sub(r"[_\s]+", " ", base).strip(" .-_")
        if not base:
            base = "video"

    if not ext:
        ext = "mp4"

    return f"{base}.{ext}"


def base_ydl_opts() -> dict:
    """Common yt-dlp options used for both metadata and download."""
    opts: dict = {
        "verbose": True,
        "ignoreerrors": True,
        "retries": 5,
        "fragment_retries": 5,
        "skip_unavailable_fragments": True,
        "source_address": "0.0.0.0",
        "geo_bypass": True,
        "geo_bypass_country": "US",
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/139.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-us,en;q=0.5",
            "Sec-Fetch-Mode": "navigate",
        },
        "noplaylist": False,  # we want playlist metadata
    }

    if COOKIES_PATH.exists():
        opts["cookiefile"] = str(COOKIES_PATH)

    return opts


def get_ydl_opts_enhanced(
    download: bool = False, format_id: str | None = None, is_audio: bool = False
) -> tuple[dict, str | None]:
    """
    Enhanced yt-dlp configuration.

    Returns (opts, download_id). For metadata, download_id is None.
    """
    global USE_SIMPLE_VERSION
    opts = base_ydl_opts()

    if not download:
        # metadata only
        opts.update(
            {
                "skip_download": True,
                "simulate": True,
                "forcejson": True,
                "extract_flat": False,
                "quiet": False,
                "no_warnings": False,
                "listformats": True,
                "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
            }
        )
        return opts, None

    # actual download
    download_id = uuid.uuid4().hex
    outtmpl = str(DOWNLOAD_DIR / f"{download_id}_%(title).100s.%(ext)s")
    opts["outtmpl"] = outtmpl

    # Choose format
    if is_audio:
        # best audio; convert to mp3
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    else:
        if format_id and format_id != "best":
            # specific video format selected by frontend
            opts["format"] = f"{format_id}+bestaudio/best"
        else:
            # best 1080p or lower
            opts["format"] = "bestvideo*+bestaudio/best"

        opts["postprocessors"] = [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ]

    logger.info("Using ENHANCED yt-dlp options")
    return opts, download_id


def get_ydl_opts_simple(
    download: bool = False, format_id: str | None = None, is_audio: bool = False
) -> tuple[dict, str | None]:
    """
    Very simple fallback options if enhanced mode fails for some user.
    """
    opts = base_ydl_opts()
    opts["http_headers"]["User-Agent"] = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    )

    if not download:
        opts.update(
            {
                "skip_download": True,
                "simulate": True,
                "forcejson": True,
                "extract_flat": False,
                "quiet": False,
                "no_warnings": False,
                "listformats": True,
                "outtmpl": str(DOWNLOAD_DIR / "%(id)s.%(ext)s"),
            }
        )
        return opts, None

    download_id = uuid.uuid4().hex
    outtmpl = str(DOWNLOAD_DIR / f"{download_id}_%(title).100s.%(ext)s")
    opts["outtmpl"] = outtmpl

    if is_audio:
        opts["format"] = "bestaudio/best"
        opts["postprocessors"] = [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ]
    else:
        if format_id and format_id != "best":
            opts["format"] = format_id
        else:
            opts["format"] = "best[height<=1080]/best"

        opts["postprocessors"] = [
            {
                "key": "FFmpegVideoConvertor",
                "preferedformat": "mp4",
            }
        ]

    logger.info("Using SIMPLE yt-dlp options")
    return opts, download_id


def final_opts(
    download: bool = False, format_id: str | None = None, is_audio: bool = False
) -> tuple[dict, str | None]:
    """
    Decide which options to use (enhanced or simple) depending on global flag.
    """
    global USE_SIMPLE_VERSION
    if USE_SIMPLE_VERSION:
        return get_ydl_opts_simple(download=download, format_id=format_id, is_audio=is_audio)
    return get_ydl_opts_enhanced(download=download, format_id=format_id, is_audio=is_audio)


def extract_formats_for_frontend(formats: list[dict]) -> list[dict]:
    """
    Convert yt-dlp 'formats' list to a trimmed version for the resolution dropdown.
    """
    cleaned: list[dict] = []
    seen_ids: set[str] = set()

    for f in formats or []:
        fmt_id = str(f.get("format_id") or f.get("id") or "")
        if not fmt_id or fmt_id in seen_ids:
            continue

        # skip weird text formats like "mhtml"
        if f.get("ext") == "mhtml":
            continue

        item = {
            "format_id": fmt_id,
            "ext": f.get("ext"),
            "height": f.get("height"),
            "width": f.get("width"),
            "fps": f.get("fps"),
            "tbr": f.get("tbr"),
            "vcodec": f.get("vcodec"),
            "acodec": f.get("acodec"),
            "resolution": f.get("resolution"),
            "quality": f.get("quality"),
        }
        cleaned.append(item)
        seen_ids.add(fmt_id)

    return cleaned


# ---------------------------------------------------------
# CLEANUP THREAD
# ---------------------------------------------------------


def cleanup_downloads_worker():
    while True:
        try:
            now = time.time()
            for path in DOWNLOAD_DIR.iterdir():
                try:
                    if not path.is_file():
                        continue
                    age = now - path.stat().st_mtime
                    if age > DOWNLOAD_TTL_SECONDS:
                        logger.info("Cleaning up old file: %s", path)
                        path.unlink(missing_ok=True)
                except Exception as e:  # noqa: BLE001
                    logger.warning("Error cleaning file %s: %s", path, e)
        except Exception as e:  # noqa: BLE001
            logger.error("Cleanup worker error: %s", e)

        time.sleep(600)  # every 10 minutes


threading.Thread(target=cleanup_downloads_worker, daemon=True).start()

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/about")
def about():
    return render_template("about.html") if (BASE_DIR / "templates" / "about.html").exists() else render_template(
        "index.html"
    )


@app.route("/api/health")
def health():
    try:
        downloads_count = len([p for p in DOWNLOAD_DIR.iterdir() if p.is_file()])
    except Exception:
        downloads_count = 0
    return jsonify(
        {
            "status": "ok",
            "cookies_exists": COOKIES_PATH.exists(),
            "downloads": downloads_count,
        }
    )


@app.route("/api/metadata", methods=["POST"])
def metadata():
    """Return video or playlist metadata."""
    global USE_SIMPLE_VERSION

    try:
        data = request.get_json(force=True) or {}
        url = data.get("url", "").strip()
        if not url:
            return jsonify({"error": "URL_REQUIRED"}), 400

        logger.info("Metadata request for URL: %s", url)

        ydl_opts, _ = final_opts(download=False)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Playlist
        if info.get("_type") in {"playlist", "multi_video"} or info.get("entries"):
            entries = info.get("entries") or []
            videos = []
            for idx, entry in enumerate(entries, start=1):
                if not entry:
                    continue
                videos.append(
                    {
                        "id": entry.get("id"),
                        "title": entry.get("title"),
                        "duration": entry.get("duration"),
                        "thumbnail": entry.get("thumbnail"),
                        "uploader": entry.get("uploader") or entry.get("channel"),
                        "index": entry.get("playlist_index") or idx,
                        "url": entry.get("webpage_url")
                        or f"https://www.youtube.com/watch?v={entry.get('id')}",
                    }
                )

            # For playlist resolution dropdown, we use first non-empty entry with formats (if present)
            playlist_formats = []
            first_with_formats = next(
                (e for e in entries if e and e.get("formats")), None
            )
            if first_with_formats:
                playlist_formats = extract_formats_for_frontend(
                    first_with_formats.get("formats")
                )

            return jsonify(
                {
                    "success": True,
                    "kind": "playlist",
                    "playlist": {
                        "id": info.get("id"),
                        "title": info.get("title") or "Playlist",
                        "uploader": info.get("uploader") or info.get("channel"),
                        "video_count": len(videos),
                        "videos": videos,
                    },
                    "formats": playlist_formats,
                }
            )

        # Single video
        video_info = {
            "id": info.get("id"),
            "title": info.get("title"),
            "duration": info.get("duration"),
            "thumbnail": info.get("thumbnail"),
            "uploader": info.get("uploader") or info.get("channel"),
            "view_count": info.get("view_count"),
            "like_count": info.get("like_count"),
            "formats": extract_formats_for_frontend(info.get("formats")),
        }

        return jsonify({"success": True, "kind": "video", "video": video_info})

    except Exception as e:  # noqa: BLE001
        logger.exception("METADATA ERROR: %s", e)

        # If enhanced mode failed once, flip the switch and try simple next time
        if not USE_SIMPLE_VERSION:
            USE_SIMPLE_VERSION = True
            logger.warning("Switching to SIMPLE yt-dlp mode due to metadata error.")

        return jsonify({"error": "METADATA_FAILED", "message": str(e)}), 500


@app.route("/api/download", methods=["POST"])
def download():
    """
    Download a single video (normal or audio-only).

    The frontend calls this for:
      - single URLs
      - each selected video inside a playlist (one by one)
    """
    global USE_SIMPLE_VERSION

    try:
        data = request.get_json(force=True) or {}
        url = data.get("url", "").strip()
        format_id = data.get("format_id") or data.get("resolution") or "best"
        kind = (data.get("kind") or "mp4").lower()
        is_audio = kind == "mp3"

        if not url:
            return jsonify({"error": "URL_REQUIRED"}), 400

        logger.info("Download request: url=%s, kind=%s, format=%s", url, kind, format_id)

        ydl_opts, download_id = final_opts(
            download=True, format_id=format_id, is_audio=is_audio
        )

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        # Determine downloaded file path
        file_path = info.get("_filename")
        if file_path:
            file_path = Path(file_path)
        else:
            # fallback: find by download_id
            candidates = list(DOWNLOAD_DIR.glob(f"{download_id}_*"))
            file_path = candidates[0] if candidates else None

        if not file_path or not file_path.exists():
            logger.error("Downloaded file not found for url=%s", url)
            return jsonify({"error": "FILE_NOT_FOUND"}), 500

        title = info.get("title") or "video"
        ext = file_path.suffix.lstrip(".").lower() or ("mp3" if is_audio else "mp4")
        download_name = safe_download_name(title, ext)

        logger.info("Sending file %s as %s", file_path, download_name)

        resp = send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype="audio/mpeg" if ext == "mp3" else "video/mp4",
            conditional=True,
        )

        # expose a short id so frontend can build /files/<id> QR link
        if download_id:
            resp.headers["X-Download-Id"] = download_id

        return resp

    except Exception as e:  # noqa: BLE001
        logger.error("DOWNLOAD ERROR: %s", e)

        # If enhanced mode failed once, flip to simple for next calls
        if not USE_SIMPLE_VERSION:
            USE_SIMPLE_VERSION = True
            logger.warning("Switching to SIMPLE yt-dlp mode due to download error.")

        return jsonify({"error": "DOWNLOAD_FAILED", "message": str(e)}), 502


@app.route("/files/<download_id>")
def serve_file_by_id(download_id: str):
    """
    Used for QR-code mobile download.

    We DON'T expose the raw filename in the URL, only the random id prefix.
    """
    try:
        candidates = sorted(DOWNLOAD_DIR.glob(f"{download_id}_*"))
        if not candidates:
            return "File expired or not found", 404

        file_path = candidates[0]
        title_part = file_path.name.split("_", 1)[-1].rsplit(".", 1)[0]
        ext = file_path.suffix.lstrip(".").lower() or "mp4"
        download_name = safe_download_name(title_part, ext)

        logger.info("QR /files request -> %s as %s", file_path, download_name)

        return send_file(
            file_path,
            as_attachment=True,
            download_name=download_name,
            mimetype="audio/mpeg" if ext == "mp3" else "video/mp4",
            conditional=True,
        )
    except Exception as e:  # noqa: BLE001
        logger.error("FILES ROUTE ERROR: %s", e)
        return "Internal error", 500


# ---------------------------------------------------------
# MAIN (for local testing)
# ---------------------------------------------------------
if __name__ == "__main__":
    # For local testing only; in production gunicorn runs this
    app.run(host="0.0.0.0", port=5000, debug=True)
