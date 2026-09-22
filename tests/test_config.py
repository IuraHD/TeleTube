import pytest

from teletube.config import Settings


def test_cloud_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("DOWNLOAD_DIR", str(tmp_path))
    monkeypatch.delenv("USE_LOCAL_API", raising=False)
    settings = Settings.from_env()
    assert not settings.local_api
    assert settings.upload_limit == 47_000_000


def test_local_api_requires_valid_url(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("USE_LOCAL_API", "true")
    monkeypatch.setenv("LOCAL_API_SERVER", "bad")
    with pytest.raises(ValueError):
        Settings.from_env()


def test_private_chat_cannot_be_cache_group(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123:abc")
    monkeypatch.setenv("CACHE_CHAT_ID", "386493800")
    with pytest.raises(ValueError, match="group"):
        Settings.from_env()
