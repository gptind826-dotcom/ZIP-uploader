"""
YouTube / audio downloader using yt-dlp.
py-tgcalls MediaStream handles ffmpeg internally, so we keep original downloaded audio file.
"""

import os
import yt_dlp
from config import DOWNLOADS_DIR


def download_audio(query: str) -> dict:
    """
    Download best audio from YouTube for the query.
    Returns dict with: title, artist, duration, file_path, thumbnail, video_id.
    """
    search_query = f"ytsearch1:{query}"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(DOWNLOADS_DIR, "%(id)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=True)
        if "entries" in info:
            info = info["entries"][0]
        video_id = info["id"]
        title = info.get("title", "Unknown")
        artist = info.get("uploader", "Unknown")
        duration = info.get("duration", 0)
        thumbnail = info.get("thumbnail", "")
        downloaded_path = ydl.prepare_filename(info)
        if not os.path.exists(downloaded_path):
            # Fallback to common extensions
            for ext in ["webm", "m4a", "mp3", "ogg", "opus", "mp4"]:
                alt = os.path.join(DOWNLOADS_DIR, f"{video_id}.{ext}")
                if os.path.exists(alt):
                    downloaded_path = alt
                    break

    return {
        "title": title,
        "artist": artist,
        "duration": _fmt_duration(duration),
        "duration_seconds": duration,
        "file_path": downloaded_path,
        "thumbnail": thumbnail,
        "video_id": video_id,
    }


def search_youtube(query: str, max_results: int = 5) -> list:
    """Return list of dicts with index, title, artist, video_id."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
    }
    search_query = f"ytsearch{max_results}:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        entries = info.get("entries", [])
    results = []
    digits = ["❶", "❷", "❸", "❹", "❺", "❻", "❼", "❽", "❾", "❿"]
    for i, entry in enumerate(entries):
        results.append({
            "index": digits[i] if i < len(digits) else f"{i+1}.",
            "title": entry.get("title", "Unknown"),
            "artist": entry.get("uploader", "Unknown"),
            "video_id": entry.get("id", ""),
        })
    return results


def _fmt_duration(seconds: int) -> str:
    if not seconds:
        return "0:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
