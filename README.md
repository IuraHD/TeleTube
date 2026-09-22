# TeleTube

TeleTube is a Telegram bot that downloads a single YouTube video at a selected resolution. It uses aiogram for Telegram updates, yt-dlp for extraction, and FFmpeg only when streams need merging or an oversized file needs splitting. It does not re-encode video.

## Run with Docker

Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN` to the token from BotFather. Then run:

```sh
docker compose up --build -d
docker compose logs -f bot
```

The default configuration uses Telegram's cloud Bot API. Each upload is kept below 47 MB to leave headroom under its 50 MB limit. Large files are split at existing keyframes where possible. Jobs use isolated temporary directories inside the container and clean them up on completion or failure.

The bot shows download progress for the current yt-dlp stream and upload progress based on bytes read from the file. A full upload bar means the bytes have been sent; the bot still waits for Telegram's confirmation before showing “Done.”

## Optional Telegram group cache

Add the bot to a private group as an admin. Send `/chatid` **inside that group**; the bot replies with its negative group ID. Put that value in `.env` as `CACHE_CHAT_ID`. The bot's private chat with you has a positive ID and cannot be used as the cache group.

Run with the cache volume so the SQLite index survives container recreation:

```sh
docker compose -f compose.yaml -f compose.cache.yaml up --build -d
```

On a cache miss, TeleTube uploads each part to the group, records its message ID in `data/cache.sqlite3`, then copies the group message to the requester. The key is the canonical YouTube video URL plus chosen resolution. On a hit it copies the saved group message without downloading or uploading the video again. If the group upload fails, delivery falls back to a direct upload. Deleting a cached group message invalidates that entry on its next use.

Without `CACHE_CHAT_ID`, no cache database is created and temporary downloads are deleted after delivery. For a local non-Docker run, `data/cache.sqlite3` persists under the project directory when caching is enabled.

To run the tests in the same Linux environment as the bot:

```sh
docker build --target test -t teletube-test .
```

The image contains Python, FFmpeg, and the bot; it does not depend on a bundled Windows executable.

## Run without Docker

Install Python 3.11 or newer, FFmpeg and FFprobe on `PATH`. On Windows or Linux, create a virtual environment and install dependencies:

```sh
python -m venv venv
venv/bin/python -m pip install -r requirements.txt    # Linux
# venv\Scripts\python.exe -m pip install -r requirements.txt  # Windows
```

Copy `.env.example` to `.env`, set the token, then run `venv/bin/python yt_downloader_bot.py` on Linux or `venv\Scripts\python.exe yt_downloader_bot.py` on Windows. The `setup` and `run_*` scripts are shortcuts for these steps. FFmpeg is a separate system dependency; the setup scripts do not delete an existing environment or download binaries.

## Local Bot API server

For uploads above the cloud limit, run a [Telegram Local Bot API server](https://github.com/tdlib/telegram-bot-api) separately and set `USE_LOCAL_API=true` and `LOCAL_API_SERVER` in `.env`. TeleTube sends multipart uploads, so the server can be on another machine or in another container. The bot caps parts at 1.9 GB under the local server's 2 GB limit. Follow Telegram's [migration instructions](https://core.telegram.org/bots/features#using-a-local-bot-api-server) when switching an existing bot from the cloud API.

## Behavior and limits

- Send a YouTube watch, Shorts, live, embed, or youtu.be video URL. Playlists and arbitrary websites are rejected.
- Choose one of the available resolutions. The bot downloads the best video at or below that height, plus audio where available.
- Two jobs can process concurrently by default; set `MAX_CONCURRENT_DOWNLOADS` to 1–8. A user can have one active job per chat.
- Compatible H.264/AAC MP4s are sent as Telegram videos with their duration and dimensions. Other formats are sent as documents with their original streams. Splitting uses stream copy, preserving codecs, resolution and frame rate. If existing keyframes cannot produce parts below the upload limit, choose a lower quality or the local Bot API.
- Cancellation interrupts yt-dlp downloads and FFmpeg work. An upload already in progress may finish before cancellation takes effect.
- Downloads and quality selections are held in memory. Restarting the bot discards pending choices and work. There is no persistent queue or retry after restart.
- Cache entries persist in SQLite when enabled; the group messages must remain available and the bot must retain access to the group.
- YouTube may change its delivery formats or require authentication for some videos. TeleTube does not accept credentials or cookies.

Check `docker compose logs bot` or the console for errors. Do not commit `.env` or download files.
