from datetime import UTC, datetime

from aiogram.types import Chat, Message, User
from httpx import AsyncClient

from app.core.db import session_scope
from app.modules.leads.dependencies import build_lead_service
from app.modules.leads.schemas import BotApplication, TelegramSender
from app.telegram.handlers.business import on_incoming_message

CLIENT = TelegramSender(chat_id=555, full_name="Иван Петров", username="ivan")


def _business_message(from_id: int, chat_id: int, text: str) -> Message:
    return Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=chat_id, type="private"),
        from_user=User(id=from_id, is_bot=False, first_name="Иван", last_name="Петров", username="ivan"),
        business_connection_id="conn",
        text=text,
    )


async def test_bot_application_becomes_tagged_lead(client: AsyncClient) -> None:
    async with session_scope() as session:
        await build_lead_service(session).create_from_bot(
            BotApplication(name="Иван", contact=None, request="Нужен сайт", service="Сайт", sender=CLIENT)
        )

    [lead] = (await client.get("/api/leads")).json()
    assert lead["source"] == "telegram_bot"
    assert lead["contact"] == "@ivan"
    assert [t["name"] for t in lead["tags"]] == ["Сайт"]

    [tag] = (await client.get("/api/tags")).json()
    assert (tag["name"], tag["lead_count"]) == ("Сайт", 1)


async def test_connected_account_groups_messages_into_one_lead(client: AsyncClient) -> None:
    for text in ("Здравствуйте!", "Сколько стоит реклама?"):
        async with session_scope() as session:
            await on_incoming_message(_business_message(555, 555, text), build_lead_service(session))

    async with session_scope() as session:
        await on_incoming_message(_business_message(999, 555, "Добрый день!"), build_lead_service(session))

    [lead] = (await client.get("/api/leads")).json()
    assert lead["source"] == "telegram_account"
    assert lead["name"] == "Иван Петров"
    assert lead["request"] == "Здравствуйте!"

    detail = (await client.get(f"/api/leads/{lead['id']}")).json()
    assert [m["text"] for m in detail["messages"]] == ["Здравствуйте!", "Сколько стоит реклама?"]
