# TeleTube

A Telegram bot for downloading individual YouTube videos. It uses aiogram for the bot, yt-dlp for downloads, and SQLite to index videos cached in an optional private Telegram group.

## Run

Install Docker with Compose, copy `.env.example` to `.env`, and set `TELEGRAM_BOT_TOKEN` to your BotFather token. Then run:

```sh
docker compose up --build -d
docker compose logs -f bot
```

The bot accepts YouTube watch, Shorts, live, embed, and `youtu.be` links. It asks for a resolution, downloads the best available video at or below that height with audio, and sends it to the requester. The status message shows download and upload progress. A completed upload bar means the file has been read; delivery is complete only after Telegram confirms the message.

Downloads use separate temporary directories and are removed after delivery. Two jobs can run at once by default (`MAX_CONCURRENT_DOWNLOADS` accepts 1–8). One user can have one active job per chat. Restarting the container clears pending jobs and quality selections.

## Cache videos in a private group

Add the bot as an admin in a private Telegram group and send `/chatid` **in that group**. Set `CACHE_CHAT_ID` in `.env` to the negative ID it returns, then restart the bot:

```sh
docker compose up -d --force-recreate
```

For a new video and resolution, the bot uploads the result to the group and saves the group message ID in a SQLite database on the `cache-index` Docker volume. Later requests copy that message to the user without downloading the video again. If the cached message has been deleted, the bot downloads the video again. Without `CACHE_CHAT_ID`, no cache is used and each download is deleted after delivery. Keep the Docker volume if you recreate the container; removing it loses the cache index.

## Video handling

TeleTube does not re-encode video. Compatible H.264/AAC MP4 files are sent as Telegram videos with their original dimensions and duration; other formats are sent as documents. FFmpeg is used to merge separate audio and video streams when needed, and to split oversized files at existing keyframes without re-encoding. If a file cannot be split below the upload limit, choose a lower resolution or configure a local Bot API server.

The default cloud Bot API configuration limits each upload part to 47 MB, leaving headroom below Telegram's 50 MB limit. For larger parts, run a [local Bot API server](https://github.com/tdlib/telegram-bot-api) separately, set `USE_LOCAL_API=true` and `LOCAL_API_SERVER` in `.env`, and follow Telegram's [migration procedure](https://core.telegram.org/bots/features#using-a-local-bot-api-server). The local-server part limit is 1.9 GB. The server must be reachable from inside the bot container; `127.0.0.1` there refers to the container itself.

Some YouTube videos may require authentication or expose formats that cannot be downloaded. The bot does not accept cookies or account credentials.

## Test

```sh
docker build --target test -t teletube-test .
```

The test stage runs the Python suite in Linux. CI runs the same command on pushes and pull requests. Do not commit `.env`, BotFather tokens, or downloaded media.
