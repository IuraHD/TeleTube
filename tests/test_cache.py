import asyncio
import json
import sqlite3

import pytest

from teletube.cache import Cache
from teletube.progress import ProgressInputFile, progress_bar


def test_cache_index_persists_and_is_scoped_to_group(tmp_path):
    path = tmp_path / "cache.sqlite3"
    first = Cache(path, -100123)
    first.put("https://www.youtube.com/watch?v=abcdefghijk", 720, [10])
    assert Cache(path, -100123).get("https://www.youtube.com/watch?v=abcdefghijk", 720) == [10]
    assert first.qualities("https://www.youtube.com/watch?v=abcdefghijk") == [720]
    assert Cache(path, -100456).qualities("https://www.youtube.com/watch?v=abcdefghijk") == []
    assert Cache(path, -100456).get("https://www.youtube.com/watch?v=abcdefghijk", 720) is None
    first.delete("https://www.youtube.com/watch?v=abcdefghijk", 720)
    assert first.get("https://www.youtube.com/watch?v=abcdefghijk", 720) is None
    assert first.qualities("https://www.youtube.com/watch?v=abcdefghijk") == []


def test_multipart_videos_are_not_eligible_for_cache(tmp_path):
    path = tmp_path / "cache.sqlite3"
    cache = Cache(path, -100123)
    url = "https://www.youtube.com/watch?v=abcdefghijk"
    with pytest.raises(ValueError):
        cache.put(url, 720, [10, 11])
    with sqlite3.connect(path) as db:
        db.execute("INSERT INTO cached_video VALUES (?, ?, ?, ?)",
                   (url, 720, -100123, json.dumps([10, 11])))
    assert cache.get(url, 720) is None
    assert cache.qualities(url) == []


def test_upload_progress_counts_file_bytes(tmp_path):
    path = tmp_path / "video.mp4"
    data = b"video" * 20000
    path.write_bytes(data)
    updates = []

    async def report(sent, total):
        updates.append((sent, total))

    async def read_file():
        media = ProgressInputFile(path, report)
        return b"".join([chunk async for chunk in media.read(None)])

    assert asyncio.run(read_file()) == data
    assert updates[-1] == (len(data), len(data))
    assert progress_bar(*updates[-1]).endswith("100%")
