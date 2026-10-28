# TeleTube

TeleTube sends individual YouTube videos to Telegram at a resolution you choose, or extracts their audio as MP3. It runs on aiogram and yt-dlp. A private Telegram group can serve as a cache, with SQLite storing the message IDs needed to reuse its media.

## Run with Docker

1. Copy `.env.example` to `.env` and set `TELEGRAM_BOT_TOKEN` to a token from [BotFather](https://t.me/BotFather).
2. Start the bot:

   ```sh
   docker compose up --build -d
   docker compose logs -f bot
   ```

Send the bot a YouTube watch, Shorts, live, embed, or `youtu.be` link. Choose an available video resolution or **MP3** in the same selector. MP3 downloads use the best available audio, convert it to 192 kbps MP3, and send it as a Telegram audio track with the title and uploader. Converting to MP3 does not improve the source audio quality. Playlists and links to other sites are rejected.

The status message shows download and upload progress. When the upload bar reaches 100%, the file has been read from disk; the bot still waits for Telegram to confirm delivery before showing that the job is done. Each job has its own temporary directory, which is removed afterward. A restart discards pending selections and downloads.

After a video is sent in a private chat, its status message offers optional 25, 50, and 100 Star support buttons. `/donate` shows the same choices at any time. Each button uses a Telegram invoice link to open the native Stars payment screen; it does not post an invoice message in the chat. Telegram sends a pre-checkout query before charging, and the bot records successful payment IDs in the SQLite database on the `cache-index` volume so a payment can be located for a refund. Donations do not change download access.

## Cache videos in a private group

Without a cache group, every request downloads and sends the video again. To reuse previous uploads:

1. Add the bot as an admin in a private Telegram group.
2. Send `/chatid` **in that group** and copy the negative ID from its reply.
3. Set `CACHE_CHAT_ID` in `.env` and recreate the container:

   ```sh
   docker compose up -d --force-recreate
   ```

On a miss, the bot uploads a complete video to the group and records its message ID in SQLite. If a video must be split to fit Telegram's upload limit, its parts are sent directly to the requester and are not cached. When you send a cached link again, the bot checks YouTube for the full quality list; if YouTube is unavailable, it offers the cached resolutions. Selecting a cached resolution copies its message to the requester without downloading the file again. The key is the YouTube video and selected resolution. If a cached group message has been deleted, the bot removes that entry and downloads the video again. A failed cache upload falls back to direct delivery.

The database lives on the `cache-index` Docker volume. Keep that volume when recreating the container; deleting it loses the index. The cached videos themselves remain in the Telegram group.

Complete MP3 tracks are cached separately from video resolutions. Internally, the existing SQLite index reserves height `0` for MP3, so no database migration is needed. Split audio tracks are delivered directly without caching. When YouTube is unavailable, the selector offers MP3 only if that track is already cached.

## Optional Cloudflare WARP proxy

If YouTube blocks the server's IP, the included Compose overlay routes yt-dlp through Cloudflare WARP's free local proxy and starts a BgUtils proof-of-origin token provider. The bot uses YouTube's mobile web client with tokens for both metadata and downloads. It uses Cloudflare's official Linux client in a separate container; Telegram traffic stays direct. Neither helper publishes a host port, and WARP's registration persists in the `warp-state` volume.

```sh
docker compose -f compose.yaml -f compose.warp.yaml up --build -d
docker compose -f compose.yaml -f compose.warp.yaml ps
```

Confirm that `warp` is healthy before sending a new link. The proxy applies to metadata, token generation, and the full media download. YouTube may also block WARP's shared exit IP, so a working test is required for each deployment. To stop using WARP, start the base Compose file again and remove `YOUTUBE_PROXY` and `YOUTUBE_POT_BASE_URL` from `.env` if you set them manually.

The image includes Deno and yt-dlp's JavaScript challenge solver. Downloader and token-provider versions are pinned in `requirements.txt` and the overlay; update those versions and rebuild when YouTube changes require an upgrade. Updating packages on the host does not update the running container.

## Configuration

| Variable | Purpose |
| --- | --- |
| `TELEGRAM_BOT_TOKEN` | Required BotFather token. |
| `CACHE_CHAT_ID` | Optional negative ID of the private cache group. Leave blank to disable caching. |
| `YOUTUBE_PROXY` | Optional HTTP, HTTPS, or SOCKS proxy URL for yt-dlp. It handles both metadata requests and video downloads; Telegram traffic stays direct. |
| `YOUTUBE_POT_BASE_URL` | Optional BgUtils token server URL. Enables the mobile web client and automatic proof-of-origin tokens. Set automatically by the WARP overlay to `http://pot:4416`; keep this unauthenticated service on a private network. |
| `MAX_CONCURRENT_DOWNLOADS` | Number of simultaneous jobs, from 1 to 8; default is 2. One user can have one active job per chat. |
| `LOG_LEVEL` | Python log level; default is `INFO`. |
| `USE_LOCAL_API`, `LOCAL_API_SERVER` | Optional [local Bot API server](https://github.com/tdlib/telegram-bot-api) for larger uploads. The server runs separately and must be reachable from the container. |

The standard Telegram Bot API permits files up to 50 MB, so TeleTube limits each cloud upload part to 47 MB. With a local Bot API server, it limits parts to 1.9 GB. Follow Telegram's [migration instructions](https://core.telegram.org/bots/features#using-a-local-bot-api-server) before switching an existing bot to a local server.

## Media handling and limits

TeleTube does not re-encode video. It sends compatible H.264/AAC MP4 files as Telegram videos, using their duration and dimensions; other formats go as documents. FFmpeg merges separate audio and video streams when necessary and splits oversized files at existing keyframes without changing their codecs. If keyframes do not allow parts below the upload limit, choose a lower resolution or use a local Bot API server.

MP3 mode downloads audio without video when YouTube provides an audio-only format. FFmpeg converts the audio to MP3 and splits oversized tracks into playable MP3 parts without another conversion. Cancellation, transfer progress, concurrent-download limits, and temporary-file cleanup also apply to MP3 jobs.

YouTube may change its formats or block some downloads, especially from cloud server IPs. Cached videos remain available when fresh extraction is blocked. If the server IP is blocked, set `YOUTUBE_PROXY` to an outbound connection that can access YouTube, then recreate the container. The proxy must be able to carry the full video download. TeleTube does not accept YouTube account credentials or cookies. For errors, inspect `docker compose logs bot`.

## Test

```sh
docker build --target test -t teletube-test .
```

The test stage runs the Python suite in Linux; GitHub Actions runs the same build on pushes and pull requests. Keep `.env`, tokens, and downloaded media out of Git.
