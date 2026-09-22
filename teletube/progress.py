"""User-visible transfer progress without claiming Telegram has confirmed delivery."""

from collections.abc import AsyncGenerator, Awaitable, Callable
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile


def progress_bar(received: int, total: int | None) -> str:
    if not total or total <= 0:
        return f"{received / 1_000_000:.1f} MB transferred"
    percent = min(100, max(0, int(received * 100 / total)))
    filled = percent // 10
    return f"[{'█' * filled}{'░' * (10 - filled)}] {percent}%"


class ProgressInputFile(FSInputFile):
    def __init__(self, path: Path, on_progress: Callable[[int, int], Awaitable[None]]):
        super().__init__(path)
        self.size = path.stat().st_size
        self.on_progress = on_progress

    async def read(self, bot: Bot) -> AsyncGenerator[bytes, None]:
        received = 0
        async for chunk in super().read(bot):
            received += len(chunk)
            yield chunk
            await self.on_progress(received, self.size)
