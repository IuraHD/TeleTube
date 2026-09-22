"""Validated runtime configuration."""

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    token: str
    download_dir: Path
    local_api: bool
    local_api_server: str
    max_concurrent_downloads: int
    upload_limit: int
    cache_chat_id: int | None = None
    cache_db_path: Path = Path("data/cache.sqlite3")

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv(override=False)
        token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        if not token or token == "replace_with_botfather_token":
            raise ValueError("Set TELEGRAM_BOT_TOKEN in .env or the environment")
        local_api = os.getenv("USE_LOCAL_API", "false").lower() in {"1", "true", "yes"}
        server = os.getenv("LOCAL_API_SERVER", "http://127.0.0.1:8081").rstrip("/")
        if local_api:
            parsed = urlsplit(server)
            if parsed.scheme not in {"http", "https"} or not parsed.hostname:
                raise ValueError("LOCAL_API_SERVER must be an HTTP(S) URL")
        concurrency = int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "2"))
        if not 1 <= concurrency <= 8:
            raise ValueError("MAX_CONCURRENT_DOWNLOADS must be between 1 and 8")
        # Leave headroom for Telegram's decimal-MB limits and multipart overhead.
        limit = 1_900_000_000 if local_api else 47_000_000
        cache_id_text = os.getenv("CACHE_CHAT_ID", "").strip()
        cache_id = int(cache_id_text) if cache_id_text else None
        if cache_id is not None and cache_id >= 0:
            raise ValueError("CACHE_CHAT_ID must be a group or supergroup ID (negative number)")
        return cls(token, Path(os.getenv("DOWNLOAD_DIR", "downloads")).resolve(),
                   local_api, server, concurrency, limit, cache_id,
                   Path(os.getenv("CACHE_DB_PATH", "data/cache.sqlite3")).resolve())
