# Contributing

TeleTube runs on Python 3.12 in Docker. To work locally, install Python 3.11 or newer and FFmpeg, then follow the setup instructions in [README.md](README.md).

Run `docker build --target test -t teletube-test .` before proposing a change. The tests cover URL validation, media splitting, cancellation, configuration, and concurrent users in the same Telegram chat. Live YouTube and Telegram calls need separate testing with your own bot token; never commit a token, cookies, or downloaded media.

Keep changes focused and describe the behavior they change. When reporting a failure, include the platform, Python or Docker version, bot log excerpt with tokens removed, and a public example URL if one is available.
