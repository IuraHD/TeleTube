import json
import subprocess
import threading

import pytest

import teletube.media as media
from teletube.media import Cancelled, available_qualities, media_details, prepare_video, video_url


@pytest.mark.parametrize("url", [
    "http://youtube.com/watch?v=abcdefghijk",
    "https://youtube.com.evil.test/watch?v=abcdefghijk",
    "https://user@youtube.com/watch?v=abcdefghijk",
    "https://youtube.com/playlist?list=PL123",
    "https://127.0.0.1/watch?v=abcdefghijk",
])
def test_rejects_non_video_and_unsafe_urls(url):
    with pytest.raises(ValueError):
        video_url(url)


def test_canonical_video_urls():
    assert video_url("https://youtu.be/abcdefghijk?t=2") == "https://www.youtube.com/watch?v=abcdefghijk"
    assert video_url("https://m.youtube.com/shorts/abcdefghijk") == "https://www.youtube.com/watch?v=abcdefghijk"


def test_unique_qualities():
    info = {"formats": [
        {"height": 720, "vcodec": "avc1", "ext": "mp4"},
        {"height": 720, "vcodec": "vp9", "ext": "webm"},
        {"height": 480, "vcodec": "avc1", "ext": "mp4"},
        {"height": None, "vcodec": "none", "ext": "m4a"},
    ]}
    assert available_qualities(info) == [720, 480]


def test_youtube_proxy_applies_to_metadata_and_download(monkeypatch, tmp_path):
    options_seen = []

    class FakeYoutubeDL:
        def __init__(self, options):
            options_seen.append(options)

        def __enter__(self):
            return self

        def __exit__(self, *_):
            pass

        def extract_info(self, url, download):
            if download:
                (tmp_path / "source.mp4").write_bytes(b"video")
            return {"title": "Fixture", "formats": []}

    monkeypatch.setenv("YOUTUBE_PROXY", "socks5://proxy.example:1080")
    monkeypatch.setattr(media, "YoutubeDL", FakeYoutubeDL)
    media.get_info("https://www.youtube.com/watch?v=abcdefghijk")
    media.download("https://www.youtube.com/watch?v=abcdefghijk", 240,
                   tmp_path, threading.Event())
    assert [options["proxy"] for options in options_seen] == [
        "socks5://proxy.example:1080", "socks5://proxy.example:1080"]


def make_video(path, seconds=5, codec="libx264"):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", f"testsrc2=size=320x180:rate=24:duration={seconds}",
                    "-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
                    "-c:v", codec, "-g", "24", "-threads", "1", "-c:a", "aac", str(path)], check=True)


def probe(path):
    result = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                             "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def test_small_mp4_is_not_reencoded(tmp_path):
    path = tmp_path / "source.mp4"
    make_video(path)
    assert prepare_video(path, 10_000_000, threading.Event()) == [path]
    assert media_details(path)["as_video"]


def test_other_codec_is_preserved_as_document(tmp_path):
    path = tmp_path / "source.mp4"
    make_video(path, codec="mpeg4")
    original = path.read_bytes()
    assert prepare_video(path, 10_000_000, threading.Event()) == [path]
    assert path.read_bytes() == original
    details = media_details(path)
    assert details["video_codec"] == "mpeg4"
    assert not details["as_video"]


def test_oversized_file_becomes_playable_segments(tmp_path):
    path = tmp_path / "source.mp4"
    make_video(path, seconds=8)
    parts = prepare_video(path, 200_000, threading.Event())
    assert len(parts) > 1
    assert all(p.stat().st_size <= 200_000 for p in parts)
    assert all(float(probe(p)["format"]["duration"]) > 0 for p in parts)
    assert all(next(s for s in probe(p)["streams"] if s["codec_type"] == "video")["codec_name"] == "h264"
               for p in parts)
    assert all(media_details(p)["width"] == 320 for p in parts)


def test_cancel_does_not_touch_other_job(tmp_path):
    first = tmp_path / "job-a"
    second = tmp_path / "job-b"
    first.mkdir()
    second.mkdir()
    make_video(first / "source.mp4")
    make_video(second / "source.mp4")
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(Cancelled):
        prepare_video(first / "source.mp4", 100_000, cancel)
    assert (second / "source.mp4").exists()
