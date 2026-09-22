# Changelog

## Unreleased

- Migrated from synchronous python-telegram-bot 13.15 to aiogram 3.31.0.
- Isolated each download in its own temporary directory and bounded concurrent work.
- Kept original media streams: compatible MP4s are sent as videos; other formats as documents. Large files are split at existing keyframes without re-encoding.
- Added download/upload progress messages and optional private-group caching with a persistent SQLite index.
- Added Linux Docker runtime and tests, including a two-user group-chat workflow.
- Removed obsolete bundled Windows Bot API binaries, installers, and release checklists. Local Bot API servers are now managed separately.

## 3.0 (July 2025)

The previous Windows-focused release used python-telegram-bot 13.15 and bundled a Windows Bot API server. Its launch and file-splitting behavior has been replaced by the implementation above.
