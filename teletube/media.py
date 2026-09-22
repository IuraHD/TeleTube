"""YouTube extraction and playable MP4 preparation."""

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlsplit

from yt_dlp import YoutubeDL


class Cancelled(Exception):
    """The requesting user cancelled the job."""


def video_url(text: str) -> str:
    """Accept a single YouTube video URL, never arbitrary yt-dlp extractors."""
    url = text.strip()
    parsed = urlsplit(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port:
        raise ValueError("Send an HTTPS YouTube video link")
    if host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0]
        else:
            parts = parsed.path.strip("/").split("/")
            video_id = parts[1] if len(parts) == 2 and parts[0] in {"shorts", "live", "embed"} else ""
    elif host in {"youtu.be", "www.youtu.be"}:
        video_id = parsed.path.strip("/")
    else:
        video_id = ""
    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Send a link to a single YouTube video")
    return f"https://www.youtube.com/watch?v={video_id}"


def available_qualities(info: dict) -> list[int]:
    return sorted({int(fmt["height"]) for fmt in info.get("formats", [])
                   if fmt.get("vcodec") not in {None, "none"} and fmt.get("height")
                   and fmt.get("ext") in {"mp4", "webm"}}, reverse=True)


def get_info(url: str) -> dict:
    options = {"quiet": True, "no_warnings": True, "noplaylist": True,
               "socket_timeout": 20, "retries": 2, "extract_flat": False}
    if proxy := os.getenv("YOUTUBE_PROXY", "").strip():
        options["proxy"] = proxy
    with YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
    if not info or info.get("_type") == "playlist":
        raise ValueError("Only single videos are supported")
    return {"title": info.get("title") or "YouTube video",
            "duration": info.get("duration"), "uploader": info.get("uploader") or "",
            "qualities": available_qualities(info)}


def _check(cancel: threading.Event) -> None:
    if cancel.is_set():
        raise Cancelled()


def download(url: str, height: int, directory: Path, cancel: threading.Event,
             on_progress: Callable[[int, int | None, str], None] | None = None) -> Path:
    _check(cancel)

    def progress(_status: dict) -> None:
        _check(cancel)
        if on_progress and _status.get("status") in {"downloading", "finished"}:
            total = _status.get("total_bytes") or _status.get("total_bytes_estimate")
            received = _status.get("downloaded_bytes") or 0
            if _status.get("status") == "finished" and total:
                received = total
            format_id = str((_status.get("info_dict") or {}).get("format_id") or "video")
            on_progress(received, total, format_id)

    options = {
        "quiet": True, "no_warnings": True, "noprogress": True, "noplaylist": True,
        "socket_timeout": 20, "retries": 2, "fragment_retries": 2,
        "outtmpl": str(directory / "source.%(ext)s"),
        "format": (f"bestvideo[height<={height}][ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/"
                   f"best[height<={height}][ext=mp4][vcodec^=avc1]/"
                   f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                   f"best[height<={height}][ext=mp4]/"
                   f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"),
        "merge_output_format": "mp4", "progress_hooks": [progress],
        "restrictfilenames": True, "overwrites": True,
    }
    if proxy := os.getenv("YOUTUBE_PROXY", "").strip():
        options["proxy"] = proxy
    with YoutubeDL(options) as ydl:
        ydl.extract_info(url, download=True)
    _check(cancel)
    candidates = [p for p in directory.glob("source.*") if p.is_file()]
    if len(candidates) != 1:
        raise RuntimeError("Download did not produce one video file")
    return candidates[0]


def _run(command: list[str], cancel: threading.Event) -> None:
    _check(cancel)
    with tempfile.TemporaryFile() as error_file:
        process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=error_file)
        while process.poll() is None:
            if cancel.is_set():
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
                raise Cancelled()
            time.sleep(0.1)
        if process.returncode:
            error_file.seek(0)
            error = error_file.read().decode("utf-8", errors="replace")[-2000:]
            raise RuntimeError(f"FFmpeg failed: {error}")


def _probe(path: Path) -> dict:
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                             "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def media_details(path: Path) -> dict:
    """Describe a file for Telegram without changing its streams."""
    info = _probe(path)
    streams = info["streams"]
    video = next((s for s in streams if s["codec_type"] == "video"), None)
    audio = next((s for s in streams if s["codec_type"] == "audio"), None)
    if not video:
        raise RuntimeError("Downloaded file has no video stream")
    return {
        "as_video": path.suffix.lower() == ".mp4" and video["codec_name"] == "h264"
                    and (audio is None or audio["codec_name"] == "aac"),
        "duration": int(float(info["format"].get("duration") or 0)),
        "width": int(video.get("width") or 0),
        "height": int(video.get("height") or 0),
        "video_codec": video["codec_name"],
        "audio_codec": audio["codec_name"] if audio else None,
    }


def prepare_video(path: Path, limit: int, cancel: threading.Event) -> list[Path]:
    """Split oversized files at existing keyframes, preserving all codecs."""
    _check(cancel)
    if path.stat().st_size <= limit:
        return [path]
    if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
        raise RuntimeError("FFmpeg and FFprobe are needed to split large files")
    duration = float(_probe(path)["format"]["duration"])
    if duration <= 0:
        raise RuntimeError("Video duration is unavailable")
    segment_seconds = max(1, int(duration * limit / path.stat().st_size * 0.7))
    extension = ".mp4" if path.suffix.lower() == ".mp4" else ".mkv"
    for _ in range(8):
        for old in path.parent.glob("part-*.*"):
            old.unlink()
        _run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(path),
              "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy", "-f", "segment",
              "-segment_time", str(segment_seconds), "-reset_timestamps", "1",
              str(path.parent / f"part-%03d{extension}")], cancel)
        parts = sorted(path.parent.glob(f"part-*{extension}"))
        if parts and len(parts) <= 100 and all(p.stat().st_size <= limit for p in parts):
            for part in parts:
                media_details(part)
            return parts
        segment_seconds = max(1, math.floor(segment_seconds * 0.7))
        if segment_seconds == 1:
            break
    raise RuntimeError("Existing keyframes cannot produce parts below the upload limit; "
                       "choose lower quality or use a local Bot API server")
