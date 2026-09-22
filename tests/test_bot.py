import asyncio
import shutil
from datetime import datetime, timezone

from aiogram import Bot
from aiogram.methods import (AnswerCallbackQuery, CopyMessage, EditMessageText,
                             SendDocument, SendMessage, SendVideo)
from aiogram.types import CallbackQuery, Chat, Message, Update, User

import teletube.bot as bot_module
from teletube.bot import create_dispatcher
from teletube.config import Settings
from teletube.cache import Cache

from test_media import make_video


def test_dispatcher_builds_with_aiogram(tmp_path):
    settings = Settings("123:abc", tmp_path, False, "http://127.0.0.1:8081", 2, 47_000_000)
    dispatcher = create_dispatcher(settings)
    assert dispatcher is not None


def test_two_users_in_same_chat_keep_separate_choices_and_files(monkeypatch, tmp_path):
    source = tmp_path / "fixture.mp4"
    make_video(source)
    edits = []
    uploads = []
    next_message = 100
    chat = Chat(id=-100123, type="supergroup")

    async def fake_call(self, method, request_timeout=None):
        nonlocal next_message
        if isinstance(method, SendMessage):
            next_message += 1
            return Message(message_id=next_message, date=datetime.now(timezone.utc),
                           chat=chat, text=method.text)
        if isinstance(method, EditMessageText):
            edits.append((method.message_id, method.text, method.reply_markup))
            return True
        if isinstance(method, SendVideo):
            uploads.append((method.chat_id, method.video.path, method))
            assert method.video.path.endswith("source.mp4")
            assert source.read_bytes() == open(method.video.path, "rb").read()
            return True
        if isinstance(method, (AnswerCallbackQuery, SendDocument)):
            return True
        raise AssertionError(type(method))

    monkeypatch.setattr(Bot, "__call__", fake_call)
    monkeypatch.setattr(bot_module, "get_info",
                        lambda url: {"title": "Fixture", "qualities": [720]})

    def fake_download(url, height, directory, cancel, on_progress=None):
        destination = directory / "source.mp4"
        shutil.copyfile(source, destination)
        return destination

    monkeypatch.setattr(bot_module, "download", fake_download)

    async def scenario():
        settings = Settings("123:abc", tmp_path / "downloads", False,
                            "http://127.0.0.1:8081", 2, 47_000_000)
        dp = create_dispatcher(settings)
        bot = Bot(settings.token)
        try:
            for user_id in (1, 2):
                user = User(id=user_id, is_bot=False, first_name=f"User{user_id}")
                message = Message(message_id=user_id, date=datetime.now(timezone.utc),
                                  chat=chat, from_user=user,
                                  text="https://youtu.be/abcdefghijk")
                await dp.feed_update(bot, Update(update_id=user_id, message=message))
                choice = edits[-1][2].inline_keyboard[0][0].callback_data
                callback_message = Message(message_id=100 + user_id,
                                           date=datetime.now(timezone.utc), chat=chat)
                callback = CallbackQuery(id=str(user_id), from_user=user,
                                         chat_instance="test", message=callback_message,
                                         data=choice)
                await dp.feed_update(bot, Update(update_id=user_id + 10,
                                                 callback_query=callback))
            for _ in range(100):
                if len(uploads) == 2:
                    break
                await asyncio.sleep(0.05)
            assert len(uploads) == 2
            assert uploads[0][1] != uploads[1][1]
            assert all(item[2].width == 320 for item in uploads)
        finally:
            await dp.emit_shutdown()
            await bot.session.close()

    asyncio.run(scenario())


def test_group_cache_reuses_telegram_message_without_redownload(monkeypatch, tmp_path):
    source = tmp_path / "fixture.mp4"
    make_video(source)
    chat = Chat(id=123, type="private")
    user = User(id=42, is_bot=False, first_name="Owner")
    edits = []
    copies = []
    uploads = []
    downloads = []
    sequence = 100

    async def fake_call(self, method, request_timeout=None):
        nonlocal sequence
        if isinstance(method, SendMessage):
            sequence += 1
            return Message(message_id=sequence, date=datetime.now(timezone.utc),
                           chat=chat, text=method.text)
        if isinstance(method, EditMessageText):
            edits.append(method)
            return True
        if isinstance(method, SendVideo):
            uploads.append(method)
            return Message(message_id=500, date=datetime.now(timezone.utc),
                           chat=Chat(id=-100999, type="supergroup"))
        if isinstance(method, CopyMessage):
            copies.append(method)
            return True
        if isinstance(method, AnswerCallbackQuery):
            return True
        raise AssertionError(type(method))

    def fake_download(url, height, directory, cancel, on_progress=None):
        downloads.append((url, height))
        path = directory / "source.mp4"
        shutil.copyfile(source, path)
        return path

    monkeypatch.setattr(Bot, "__call__", fake_call)
    monkeypatch.setattr(bot_module, "get_info",
                        lambda url: {"title": "Fixture", "qualities": [240]})
    monkeypatch.setattr(bot_module, "download", fake_download)

    async def scenario():
        settings = Settings("123:abc", tmp_path / "downloads", False,
                            "http://127.0.0.1:8081", 2, 47_000_000,
                            -100999, tmp_path / "data" / "cache.sqlite3")
        dp = create_dispatcher(settings)
        bot = Bot(settings.token)
        try:
            for request in (1, 2):
                message = Message(message_id=request, date=datetime.now(timezone.utc),
                                  chat=chat, from_user=user,
                                  text="https://youtu.be/abcdefghijk")
                await dp.feed_update(bot, Update(update_id=request, message=message))
                choice = next(e.reply_markup.inline_keyboard[0][0].callback_data
                              for e in reversed(edits) if e.reply_markup and
                              e.reply_markup.inline_keyboard[0][0].callback_data.startswith("q:"))
                callback = CallbackQuery(id=str(request), from_user=user,
                                         chat_instance="test",
                                         message=Message(message_id=100 + request,
                                                         date=datetime.now(timezone.utc), chat=chat),
                                         data=choice)
                await dp.feed_update(bot, Update(update_id=10 + request,
                                                 callback_query=callback))
                for _ in range(100):
                    if len(copies) == request and any(e.text == "Done." for e in edits[-4:]):
                        break
                    await asyncio.sleep(0.05)
                assert len(copies) == request
                await asyncio.sleep(0.05)
            assert len(downloads) == 1
            assert len(uploads) == 1
            assert uploads[0].chat_id == -100999
            assert all(c.from_chat_id == -100999 and c.chat_id == 123 for c in copies)
            assert Cache(settings.cache_db_path, -100999).get(
                "https://www.youtube.com/watch?v=abcdefghijk", 240) == [500]
        finally:
            await dp.emit_shutdown()
            await bot.session.close()

    asyncio.run(scenario())


def test_cached_video_is_offered_when_youtube_is_unavailable(monkeypatch, tmp_path):
    chat = Chat(id=123, type="private")
    user = User(id=42, is_bot=False, first_name="Owner")
    edits = []
    copies = []
    sequence = 100

    async def fake_call(self, method, request_timeout=None):
        nonlocal sequence
        if isinstance(method, SendMessage):
            sequence += 1
            return Message(message_id=sequence, date=datetime.now(timezone.utc),
                           chat=chat, text=method.text)
        if isinstance(method, EditMessageText):
            edits.append(method)
            return True
        if isinstance(method, CopyMessage):
            copies.append(method)
            return True
        if isinstance(method, AnswerCallbackQuery):
            return True
        raise AssertionError(type(method))

    def unavailable(*args, **kwargs):
        raise RuntimeError("YouTube is unavailable")

    def no_download(*args, **kwargs):
        raise AssertionError("A cached quality must not download")

    monkeypatch.setattr(Bot, "__call__", fake_call)
    monkeypatch.setattr(bot_module, "get_info", unavailable)
    monkeypatch.setattr(bot_module, "download", no_download)

    async def scenario():
        settings = Settings("123:abc", tmp_path / "downloads", False,
                            "http://127.0.0.1:8081", 2, 47_000_000,
                            -100999, tmp_path / "data" / "cache.sqlite3")
        url = "https://www.youtube.com/watch?v=abcdefghijk"
        Cache(settings.cache_db_path, -100999).put(url, 240, [500])
        dp = create_dispatcher(settings)
        bot = Bot(settings.token)
        try:
            message = Message(message_id=1, date=datetime.now(timezone.utc),
                              chat=chat, from_user=user,
                              text="https://youtu.be/abcdefghijk")
            await dp.feed_update(bot, Update(update_id=1, message=message))
            choice = edits[-1].reply_markup.inline_keyboard[0][0].callback_data
            callback = CallbackQuery(id="1", from_user=user, chat_instance="test",
                                     message=Message(message_id=101,
                                                     date=datetime.now(timezone.utc), chat=chat),
                                     data=choice)
            await dp.feed_update(bot, Update(update_id=2, callback_query=callback))
            for _ in range(100):
                if copies:
                    break
                await asyncio.sleep(0.05)
            assert len(copies) == 1
            assert copies[0].from_chat_id == -100999
        finally:
            await dp.emit_shutdown()
            await bot.session.close()

    asyncio.run(scenario())


def test_cached_link_still_offers_uncached_qualities(monkeypatch, tmp_path):
    chat = Chat(id=123, type="private")
    user = User(id=42, is_bot=False, first_name="Owner")
    edits = []

    async def fake_call(self, method, request_timeout=None):
        if isinstance(method, SendMessage):
            return Message(message_id=101, date=datetime.now(timezone.utc),
                           chat=chat, text=method.text)
        if isinstance(method, EditMessageText):
            edits.append(method)
            return True
        raise AssertionError(type(method))

    monkeypatch.setattr(Bot, "__call__", fake_call)
    monkeypatch.setattr(bot_module, "get_info",
                        lambda url: {"title": "Fixture", "qualities": [1080, 240]})

    async def scenario():
        settings = Settings("123:abc", tmp_path / "downloads", False,
                            "http://127.0.0.1:8081", 2, 47_000_000,
                            -100999, tmp_path / "data" / "cache.sqlite3")
        Cache(settings.cache_db_path, -100999).put(
            "https://www.youtube.com/watch?v=abcdefghijk", 240, [500])
        dp = create_dispatcher(settings)
        bot = Bot(settings.token)
        try:
            message = Message(message_id=1, date=datetime.now(timezone.utc),
                              chat=chat, from_user=user,
                              text="https://youtu.be/abcdefghijk")
            await dp.feed_update(bot, Update(update_id=1, message=message))
            buttons = edits[-1].reply_markup.inline_keyboard
            assert [row[0].text for row in buttons] == ["1080p", "240p"]
        finally:
            await dp.emit_shutdown()
            await bot.session.close()

    asyncio.run(scenario())


def test_split_video_is_delivered_without_caching_parts(monkeypatch, tmp_path):
    source = tmp_path / "fixture.mp4"
    make_video(source)
    chat = Chat(id=123, type="private")
    user = User(id=42, is_bot=False, first_name="Owner")
    edits = []
    uploads = []

    async def fake_call(self, method, request_timeout=None):
        if isinstance(method, SendMessage):
            return Message(message_id=101, date=datetime.now(timezone.utc),
                           chat=chat, text=method.text)
        if isinstance(method, EditMessageText):
            edits.append(method)
            return True
        if isinstance(method, SendVideo):
            uploads.append(method)
            return Message(message_id=500 + len(uploads), date=datetime.now(timezone.utc),
                           chat=chat)
        if isinstance(method, AnswerCallbackQuery):
            return True
        raise AssertionError(type(method))

    def fake_download(url, height, directory, cancel, on_progress=None):
        destination = directory / "source.mp4"
        shutil.copyfile(source, destination)
        return destination

    monkeypatch.setattr(Bot, "__call__", fake_call)
    monkeypatch.setattr(bot_module, "get_info",
                        lambda url: {"title": "Fixture", "qualities": [240]})
    monkeypatch.setattr(bot_module, "download", fake_download)
    monkeypatch.setattr(bot_module, "prepare_video", lambda path, limit, cancel: [path, path])

    async def scenario():
        settings = Settings("123:abc", tmp_path / "downloads", False,
                            "http://127.0.0.1:8081", 2, 47_000_000,
                            -100999, tmp_path / "data" / "cache.sqlite3")
        dp = create_dispatcher(settings)
        bot = Bot(settings.token)
        try:
            message = Message(message_id=1, date=datetime.now(timezone.utc),
                              chat=chat, from_user=user,
                              text="https://youtu.be/abcdefghijk")
            await dp.feed_update(bot, Update(update_id=1, message=message))
            choice = edits[-1].reply_markup.inline_keyboard[0][0].callback_data
            callback = CallbackQuery(id="1", from_user=user, chat_instance="test",
                                     message=Message(message_id=101,
                                                     date=datetime.now(timezone.utc), chat=chat),
                                     data=choice)
            await dp.feed_update(bot, Update(update_id=2, callback_query=callback))
            for _ in range(100):
                if len(uploads) == 2:
                    break
                await asyncio.sleep(0.05)
            assert [item.chat_id for item in uploads] == [123, 123]
            assert Cache(settings.cache_db_path, -100999).get(
                "https://www.youtube.com/watch?v=abcdefghijk", 240) is None
        finally:
            await dp.emit_shutdown()
            await bot.session.close()

    asyncio.run(scenario())
