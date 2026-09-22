"""Persistent index of videos stored in a private Telegram group."""

import json
import sqlite3
from pathlib import Path


class Cache:
    def __init__(self, path: Path, chat_id: int):
        self.path = path
        self.chat_id = chat_id
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS cached_video (
                video_url TEXT NOT NULL,
                height INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                message_ids TEXT NOT NULL,
                PRIMARY KEY (video_url, height, chat_id)
            )""")

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path, timeout=30)

    def get(self, video_url: str, height: int) -> list[int] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT message_ids FROM cached_video WHERE video_url=? AND height=? AND chat_id=?",
                (video_url, height, self.chat_id),
            ).fetchone()
        if not row:
            return None
        ids = json.loads(row[0])
        return ids if isinstance(ids, list) and ids and all(isinstance(i, int) and i > 0 for i in ids) else None

    def put(self, video_url: str, height: int, message_ids: list[int]) -> None:
        if not message_ids or any(i <= 0 for i in message_ids):
            raise ValueError("Only fully sent Telegram messages can be cached")
        with self._connect() as db:
            db.execute("""INSERT OR REPLACE INTO cached_video
                          (video_url, height, chat_id, message_ids) VALUES (?, ?, ?, ?)""",
                       (video_url, height, self.chat_id, json.dumps(message_ids)))

    def delete(self, video_url: str, height: int) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM cached_video WHERE video_url=? AND height=? AND chat_id=?",
                       (video_url, height, self.chat_id))
