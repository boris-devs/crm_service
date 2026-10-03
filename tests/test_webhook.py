from datetime import UTC, datetime

import pytest
from aiogram import Bot
from aiogram.methods import SetWebhook
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.config import BotMode, Settings
from app.telegram.bot import create_dispatcher
from app.telegram.webhook import WEBHOOK_PATH, TelegramWebhook, create_webhook
from tests.fakes import FakeSession

SECRET = "test-secret"
HEADERS = {"X-Telegram-Bot-Api-Secret-Token": SECRET}


@pytest.fixture
def telegram() -> tuple[TelegramWebhook, FakeSession]:
    session = FakeSession()
    webhook = TelegramWebhook(Bot("42:TEST", session=session), create_dispatcher(Settings()), SECRET)
    return webhook, session


@pytest.fixture
async def webhook_client(telegram: tuple[TelegramWebhook, FakeSession]):
    app = FastAPI()
    app.include_router(telegram[0].build_router())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://crm.example") as http:
        yield http


def _business_update(text: str) -> dict:
    user = {"id": 555, "is_bot": False, "first_name": "Иван", "username": "ivan"}
    return {
        "update_id": 1,
        "business_message": {
            "message_id": 1,
            "date": int(datetime.now(UTC).timestamp()),
            "chat": {"id": 555, "type": "private"},
            "from": user,
            "business_connection_id": "conn",
            "text": text,
        },
    }


async def test_rejects_requests_without_secret(webhook_client: AsyncClient) -> None:
    response = await webhook_client.post(WEBHOOK_PATH, json=_business_update("Привет"))
    assert response.status_code == 403
    wrong = await webhook_client.post(
        WEBHOOK_PATH, json=_business_update("Привет"), headers={"X-Telegram-Bot-Api-Secret-Token": "nope"}
    )
    assert wrong.status_code == 403


async def test_update_becomes_lead(webhook_client: AsyncClient, client: AsyncClient) -> None:
    response = await webhook_client.post(WEBHOOK_PATH, json=_business_update("Нужна реклама"), headers=HEADERS)
    assert response.status_code == 200

    [lead] = (await client.get("/api/leads")).json()
    assert (lead["source"], lead["request"]) == ("telegram_account", "Нужна реклама")


async def test_register_sets_webhook_with_secret(telegram: tuple[TelegramWebhook, FakeSession]) -> None:
    webhook, session = telegram
    await webhook.register("https://crm.onrender.com/")

    [set_webhook] = [m for m in session.methods if isinstance(m, SetWebhook)]
    assert set_webhook.url == "https://crm.onrender.com/telegram/webhook"
    assert set_webhook.secret_token == SECRET
    assert "business_message" in set_webhook.allowed_updates


def test_webhook_only_in_webhook_mode() -> None:
    assert create_webhook(Settings(bot_token="42:TEST", bot_mode=BotMode.POLLING)) is None
    with pytest.raises(RuntimeError, match="WEBHOOK_BASE_URL"):
        create_webhook(Settings(bot_token="42:TEST", bot_mode=BotMode.WEBHOOK, WEBHOOK_BASE_URL=None))
