import asyncio

from teletube.cache import Cache
from teletube.progress import ProgressInputFile, progress_bar


def test_cache_index_persists_and_is_scoped_to_group(tmp_path):
    path = tmp_path / "cache.sqlite3"
    first = Cache(path, -100123)
    first.put("https://www.youtube.com/watch?v=abcdefghijk", 720, [10, 11])
    assert Cache(path, -100123).get("https://www.youtube.com/watch?v=abcdefghijk", 720) == [10, 11]
    assert first.qualities("https://www.youtube.com/watch?v=abcdefghijk") == [720]
    assert Cache(path, -100456).qualities("https://www.youtube.com/watch?v=abcdefghijk") == []
    assert Cache(path, -100456).get("https://www.youtube.com/watch?v=abcdefghijk", 720) is None
    first.delete("https://www.youtube.com/watch?v=abcdefghijk", 720)
    assert first.get("https://www.youtube.com/watch?v=abcdefghijk", 720) is None
    assert first.qualities("https://www.youtube.com/watch?v=abcdefghijk") == []


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
