# TeleTube

TeleTube sends individual YouTube videos to Telegram at a resolution you choose. It runs on aiogram and yt-dlp. A private Telegram group can serve as a cache, with SQLite storing the message IDs needed to reuse its videos.

## Run with Docker

1. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN` to a token from [BotFather](https://t.me/BotFather).
2. Start the bot:

   ```sh
   docker compose up --build -d
   docker compose logs -f bot
   ```

Send the bot a YouTube watch, Shorts, live, embed, or `youtu.be` link. It offers the available resolutions, downloads the selected video, and sends it back. Playlists and links to other sites are rejected.

The status message shows download and upload progress. When the upload bar reaches 100%, the file has been read from disk; the bot still waits for Telegram to confirm delivery before showing that the job is done. Each job has its own temporary directory, which is removed afterward. A restart discards pending selections and downloads.

## Cache videos in a private group

Without a cache group, every request downloads and sends the video again. To reuse previous uploads:

1. Add the bot as an admin in a private Telegram group.
2. Send `/chatid` **in that group** and copy the negative ID from its reply.
3. Set `CACHE_CHAT_ID` in `.env` and recreate the container:

   ```sh
   docker compose up -d --force-recreate
   ```

On a miss, the bot uploads the video or its parts to the group and records their message IDs in SQLite. On a hit, it offers the cached resolutions without contacting YouTube, then copies the selected messages to the requester. The key is the YouTube video and selected resolution. If a cached group message has been deleted, the bot removes that entry and downloads the video again. A failed cache upload falls back to direct delivery.

The database lives on the `cache-index` Docker volume. Keep that volume when recreating the container; deleting it loses the index. The cached videos themselves remain in the Telegram group.

## Configuration

| Variable | Purpose |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Required BotFather token. |
| `CACHE_CHAT_ID` | Optional negative ID of the private cache group. Leave blank to disable caching. |
| `MAX_CONCURRENT_DOWNLOADS` | Number of simultaneous jobs, from 1 to 8; default is 2. One user can have one active job per chat. |
| `LOG_LEVEL` | Python log level; default is `INFO`. |
| `USE_LOCAL_API`, `LOCAL_API_SERVER` | Optional [local Bot API server](https://github.com/tdlib/telegram-bot-api) for larger uploads. The server runs separately and must be reachable from the container. |

The standard Telegram Bot API permits files up to 50 MB, so TeleTube limits each cloud upload part to 47 MB. With a local Bot API server, it limits parts to 1.9 GB. Follow Telegram's [migration instructions](https://core.telegram.org/bots/features#using-a-local-bot-api-server) before switching an existing bot to a local server.

## Media handling and limits

TeleTube does not re-encode video. It sends compatible H.264/AAC MP4 files as Telegram videos, using their duration and dimensions; other formats go as documents. FFmpeg merges separate audio and video streams when necessary and splits oversized files at existing keyframes without changing their codecs. If keyframes do not allow parts below the upload limit, choose a lower resolution or use a local Bot API server.

YouTube may change its formats or block some downloads, especially from cloud server IPs. Cached videos remain available when fresh extraction is blocked. TeleTube does not accept account credentials or cookies. For errors, inspect `docker compose logs bot`.

## Test

```sh
docker build --target test -t teletube-test .
```

The test stage runs the Python suite in Linux; GitHub Actions runs the same build on pushes and pull requests. Keep `.env`, tokens, and downloaded media out of Git.
