"""Aiogram polling bot and per-user download lifecycle."""

import asyncio
import html
import logging
import os
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.client.telegram import TelegramAPIServer
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from teletube.cache import Cache
from teletube.config import Settings
from teletube.media import Cancelled, download, get_info, media_details, prepare_video, video_url
from teletube.progress import ProgressInputFile, progress_bar

logger = logging.getLogger(__name__)


@dataclass
class Job:
    nonce: str
    url: str
    title: str
    qualities: list[int]
    cancel: threading.Event
    duration: int | None = None
    uploader: str = ""
    task: asyncio.Task | None = None
    stage: str = "choice"


def keyboard(job: Job) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{height}p", callback_data=f"q:{job.nonce}:{height}")]
        for height in job.qualities[:12]
    ])


def cancel_keyboard(job: Job) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Cancel", callback_data=f"c:{job.nonce}")]
    ])


def create_dispatcher(settings: Settings) -> Dispatcher:
    router = Router()
    jobs: dict[tuple[int, int], Job] = {}
    running: set[asyncio.Task] = set()
    semaphore = asyncio.Semaphore(settings.max_concurrent_downloads)
    cache = Cache(settings.cache_db_path, settings.cache_chat_id) if settings.cache_chat_id else None
    cache_locks: dict[tuple[str, int], asyncio.Lock] = {}
    settings.download_dir.mkdir(parents=True, exist_ok=True)

    async def status(bot: Bot, chat_id: int, message_id: int, text: str,
                     reply_markup: InlineKeyboardMarkup | None = None) -> None:
        try:
            await bot.edit_message_text(text, chat_id=chat_id, message_id=message_id,
                                        reply_markup=reply_markup, parse_mode="HTML")
        except Exception:
            logger.warning("Could not edit status message", exc_info=True)

    async def answer_callback(query: CallbackQuery, text: str | None = None,
                              show_alert: bool = False) -> bool:
        try:
            await query.answer(text, show_alert=show_alert)
            return True
        except TelegramBadRequest as error:
            if "query is too old" in str(error):
                logger.info("Ignored expired callback in chat %s", query.message.chat.id if query.message else "?")
                return False
            raise

    async def send_part(bot: Bot, destination: int, part: Path, caption: str,
                        index: int, count: int, job: Job, chat_id: int,
                        message_id: int, label: str) -> Message:
        last_update = 0.0
        last_text = ""
        job.stage = "upload"
        await status(bot, chat_id, message_id,
                     f"{label} part {index}/{count}…", cancel_keyboard(job))

        async def report(sent: int, total: int) -> None:
            nonlocal last_update, last_text
            if job.cancel.is_set():
                return
            now = time.monotonic()
            if sent < total and now - last_update < 1.5:
                return
            suffix = " · waiting for Telegram" if sent >= total else ""
            text = f"{label} part {index}/{count}\n{progress_bar(sent, total)}{suffix}"
            if text == last_text:
                return
            last_update, last_text = now, text
            await status(bot, chat_id, message_id, text, cancel_keyboard(job))

        details = await asyncio.to_thread(media_details, part)
        media = ProgressInputFile(part, report)
        if details["as_video"]:
            return await bot.send_video(destination, media, caption=caption,
                                        duration=details["duration"], width=details["width"],
                                        height=details["height"], supports_streaming=True,
                                        request_timeout=1800)
        return await bot.send_document(destination, media, caption=caption,
                                       request_timeout=1800)

    async def perform(bot: Bot, chat_id: int, user_id: int, message_id: int,
                      job: Job, height: int) -> None:
        key = (chat_id, user_id)
        lock = cache_locks.setdefault((job.url, height), asyncio.Lock()) if cache else asyncio.Lock()
        try:
            async with lock:
                if job.cancel.is_set():
                    raise Cancelled()
                if cache and chat_id != cache.chat_id:
                    saved = cache.get(job.url, height)
                    if saved:
                        logger.info("Cache hit for chat %s at %sp (%s part(s))",
                                    chat_id, height, len(saved))
                        job.stage = "copy"
                        await status(bot, chat_id, message_id, "Sending from cache…")
                        copied = 0
                        try:
                            for cached_id in saved:
                                if job.cancel.is_set():
                                    raise Cancelled()
                                await bot.copy_message(chat_id, cache.chat_id, cached_id)
                                copied += 1
                        except TelegramBadRequest:
                            logger.warning("Cached message is unavailable; invalidating entry", exc_info=True)
                            cache.delete(job.url, height)
                            if copied:
                                raise RuntimeError("Cache delivery stopped after some parts")
                        else:
                            logger.info("Delivered cached video to chat %s", chat_id)
                            await status(bot, chat_id, message_id, "Sent from cache.")
                            return

                async with semaphore:
                    if job.cancel.is_set():
                        raise Cancelled()
                    job.stage = "download"
                    logger.info("Starting %sp download for chat %s user %s", height, chat_id, user_id)
                    await status(bot, chat_id, message_id,
                                 f"Downloading {height}p…", cancel_keyboard(job))
                    loop = asyncio.get_running_loop()
                    progress_state = {"format": None, "stream": 0,
                                      "last_time": 0.0, "last_text": ""}

                    async def show_download(text: str) -> None:
                        if job.stage == "download" and not job.cancel.is_set():
                            await status(bot, chat_id, message_id, text, cancel_keyboard(job))

                    def report_download(received: int, total: int | None, format_id: str) -> None:
                        if job.cancel.is_set():
                            return
                        if format_id != progress_state["format"]:
                            progress_state.update(format=format_id, stream=progress_state["stream"] + 1,
                                                  last_time=0.0, last_text="")
                        now = time.monotonic()
                        pct = min(100, int(received * 100 / total)) if total else -1
                        if now - progress_state["last_time"] < 1.5 and pct != 100:
                            return
                        label = f"Downloading stream {progress_state['stream']}\n"
                        text = label + progress_bar(received, total)
                        if text == progress_state["last_text"]:
                            return
                        progress_state.update(last_time=now, last_text=text)
                        loop.call_soon_threadsafe(lambda: asyncio.create_task(show_download(text)))

                    with tempfile.TemporaryDirectory(prefix="teletube-", dir=settings.download_dir) as temp:
                        source = await asyncio.to_thread(download, job.url, height, Path(temp),
                                                         job.cancel, report_download)
                        logger.info("Download complete for chat %s; bytes=%s", chat_id,
                                    source.stat().st_size)
                        job.stage = "prepare"
                        await status(bot, chat_id, message_id,
                                     "Checking upload size…", cancel_keyboard(job))
                        parts = await asyncio.to_thread(prepare_video, source,
                                                        settings.upload_limit, job.cancel)
                        logger.info("Prepared %s part(s) for chat %s", len(parts), chat_id)
                        saved_ids = []
                        if cache and chat_id != cache.chat_id:
                            try:
                                for index, part in enumerate(parts, 1):
                                    if job.cancel.is_set():
                                        raise Cancelled()
                                    caption = job.title[:900] + (f" ({index}/{len(parts)})"
                                                               if len(parts) > 1 else "")
                                    sent = await send_part(bot, cache.chat_id, part, caption, index,
                                                           len(parts), job, chat_id, message_id,
                                                           "Uploading to cache")
                                    saved_ids.append(sent.message_id)
                                cache.put(job.url, height, saved_ids)
                                logger.info("Stored %s part(s) in cache group %s",
                                            len(saved_ids), cache.chat_id)
                            except Cancelled:
                                raise
                            except Exception:
                                logger.warning("Cache upload failed; delivering directly", exc_info=True)
                                saved_ids.clear()

                        copy_failed = False
                        for index, part in enumerate(parts, 1):
                            if job.cancel.is_set():
                                raise Cancelled()
                            if saved_ids and not copy_failed:
                                job.stage = "copy"
                                await status(bot, chat_id, message_id,
                                             f"Sending cached part {index}/{len(parts)}…")
                                try:
                                    await bot.copy_message(chat_id, cache.chat_id, saved_ids[index - 1])
                                    continue
                                except TelegramBadRequest:
                                    cache.delete(job.url, height)
                                    copy_failed = True
                                    logger.warning("Cache copy failed; using local file", exc_info=True)
                            caption = job.title[:900] + (f" ({index}/{len(parts)})"
                                                       if len(parts) > 1 else "")
                            await send_part(bot, chat_id, part, caption, index, len(parts), job,
                                            chat_id, message_id, "Uploading")
                            logger.info("Delivered part %s/%s for chat %s", index, len(parts), chat_id)
                    if job.cancel.is_set():
                        raise Cancelled()
                    await status(bot, chat_id, message_id, "Done.")
        except Cancelled:
            await status(bot, chat_id, message_id, "Cancelled.")
        except asyncio.CancelledError:
            await status(bot, chat_id, message_id,
                         "Stopped before Telegram confirmed delivery. Check the chat before retrying.")
            raise
        except Exception as error:
            logger.exception("Download or upload failed for chat %s", chat_id)
            if job.cancel.is_set():
                explanation = "Cancelled."
            elif "Existing keyframes" in str(error):
                explanation = ("This video cannot be split without changing its streams. "
                               "Try a lower quality or a local Bot API server.")
            else:
                explanation = "Could not download or send this video. Try another quality or link."
            await status(bot, chat_id, message_id, explanation)
        finally:
            if jobs.get(key) is job:
                jobs.pop(key, None)

    @router.message(CommandStart())
    async def start(message: Message) -> None:
        await message.answer("Send a YouTube video link and choose a quality.")

    @router.message(Command("chatid"))
    async def chatid(message: Message) -> None:
        if message.chat.type in {"group", "supergroup"}:
            logger.info("Received /chatid in group %s", message.chat.id)
            await message.answer(f"This group's chat ID is <code>{message.chat.id}</code>.",
                                 parse_mode="HTML")
        else:
            await message.answer("Send /chatid inside the private cache group.")

    @router.message(F.text)
    async def link(message: Message) -> None:
        if not message.from_user or not message.text:
            return
        key = (message.chat.id, message.from_user.id)
        current = jobs.get(key)
        if current and current.task and not current.task.done():
            await message.answer("Your previous video is still processing. Cancel it first.")
            return
        try:
            url = video_url(message.text)
        except ValueError as error:
            await message.answer(str(error))
            return
        notice = await message.answer("Checking available qualities…")
        nonce = uuid.uuid4().hex[:12]
        pending = Job(nonce, url, "", [], threading.Event())
        jobs[key] = pending
        try:
            async with semaphore:
                info = await asyncio.to_thread(get_info, url)
            if jobs.get(key) is not pending:
                return
            if not info["qualities"]:
                raise ValueError("No downloadable video qualities were found")
            job = Job(nonce, url, info["title"], info["qualities"], threading.Event(),
                      info.get("duration"), info.get("uploader", ""))
            jobs[key] = job
            logger.info("Offered %s quality choices for chat %s user %s", len(job.qualities),
                        key[0], key[1])
            details = []
            if job.uploader:
                details.append(html.escape(job.uploader[:100]))
            if job.duration:
                minutes, seconds = divmod(int(job.duration), 60)
                details.append(f"{minutes}:{seconds:02d}")
            summary = " · ".join(details)
            if summary:
                summary += "\n"
            await status(message.bot, message.chat.id, notice.message_id,
                         f"<b>{html.escape(job.title[:200])}</b>\n"
                         f"{summary}Choose quality:", keyboard(job))
        except Exception:
            logger.exception("Failed to read video metadata")
            await status(message.bot, message.chat.id, notice.message_id,
                         "Could not read this video's details. Check the link and try again.")
            if jobs.get(key) is pending:
                jobs.pop(key, None)

    @router.callback_query(F.data.startswith("q:"))
    async def choose(query: CallbackQuery) -> None:
        if not query.message or not query.data:
            await answer_callback(query)
            return
        key = (query.message.chat.id, query.from_user.id)
        job = jobs.get(key)
        parts = query.data.split(":")
        if not job or len(parts) != 3 or parts[1] != job.nonce or not parts[2].isdigit():
            await answer_callback(query, "This choice expired. Send the link again.", show_alert=True)
            return
        height = int(parts[2])
        if height not in job.qualities or job.task:
            await answer_callback(query, "This choice is no longer available.", show_alert=True)
            return
        if not await answer_callback(query):
            return
        logger.info("Quality %sp chosen for chat %s user %s", height, key[0], key[1])
        task = asyncio.create_task(perform(query.bot, key[0], key[1],
                                           query.message.message_id, job, height))
        job.task = task
        running.add(task)
        task.add_done_callback(running.discard)

    @router.callback_query(F.data.startswith("c:"))
    async def cancel(query: CallbackQuery) -> None:
        if not query.message or not query.data:
            await answer_callback(query)
            return
        key = (query.message.chat.id, query.from_user.id)
        job = jobs.get(key)
        if not job or query.data != f"c:{job.nonce}":
            await answer_callback(query, "This job has finished.")
            return
        job.cancel.set()
        await answer_callback(query, "Stopping the job…")
        await status(query.bot, key[0], query.message.message_id,
                     "Stopping after the current operation…")

    dp = Dispatcher()
    dp.include_router(router)

    async def shutdown() -> None:
        for job in jobs.values():
            job.cancel.set()
        if running:
            _, pending = await asyncio.wait(running, timeout=20)
            for task in pending:
                task.cancel()
            await asyncio.gather(*running, return_exceptions=True)

    dp.shutdown.register(shutdown)
    return dp


async def run(settings: Settings) -> None:
    session = None
    if settings.local_api:
        session = AiohttpSession(api=TelegramAPIServer.from_base(settings.local_api_server))
    bot = Bot(settings.token, session=session)
    try:
        await create_dispatcher(settings).start_polling(bot, tasks_concurrency_limit=32)
    finally:
        await bot.session.close()


def main() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper(),
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    asyncio.run(run(Settings.from_env()))
