import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    "url",
    [
        "postgres://u:p@host:5432/db",
        "postgresql://u:p@host:5432/db",
        "postgresql+asyncpg://u:p@host:5432/db",
    ],
)
def test_database_url_uses_async_driver(url: str) -> None:
    assert Settings(DATABASE_URL=url).database_url == "postgresql+asyncpg://u:p@host:5432/db"


def test_webhook_base_url_falls_back_to_render(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WEBHOOK_BASE_URL", raising=False)
    monkeypatch.setenv("RENDER_EXTERNAL_URL", "https://crm.onrender.com")
    assert Settings().webhook_base_url == "https://crm.onrender.com"
