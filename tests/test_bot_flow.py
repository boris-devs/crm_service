from datetime import UTC, datetime

from aiogram import Bot
from aiogram.types import CallbackQuery, Chat, Message, Update, User
from httpx import AsyncClient

from app.core.config import Settings
from app.telegram.bot import create_dispatcher
from app.telegram.keyboards import ServiceCallback
from tests.fakes import FakeSession
from tests.fakes import ids as _ids

USER = User(id=777, is_bot=False, first_name="Анна", username="anna")
CHAT = Chat(id=777, type="private")


def _message(text: str) -> Update:
    message = Message(message_id=next(_ids), date=datetime.now(UTC), chat=CHAT, from_user=USER, text=text)
    return Update(update_id=next(_ids), message=message)


def _callback(data: str) -> Update:
    message = Message(message_id=next(_ids), date=datetime.now(UTC), chat=CHAT, text="Какая услуга?")
    query = CallbackQuery(id="cb", from_user=USER, chat_instance="ci", message=message, data=data)
    return Update(update_id=next(_ids), callback_query=query)


async def test_bot_dialogue_creates_tagged_lead(client: AsyncClient) -> None:
    session = FakeSession()
    bot = Bot("42:TEST", session=session)
    dispatcher = create_dispatcher(Settings(bot_services=["Сайт", "SMM"]))

    for update in (
        _message("/start"),
        _message("Анна"),
        _message("anna@example.com"),
        _callback(ServiceCallback(index=1).pack()),
        _message("Ведение Instagram на 3 месяца"),
    ):
        await dispatcher.feed_update(bot, update)

    [lead] = (await client.get("/api/leads")).json()
    assert lead["name"] == "Анна"
    assert lead["contact"] == "anna@example.com"
    assert lead["request"] == "Ведение Instagram на 3 месяца"
    assert lead["source"] == "telegram_bot"
    assert [t["name"] for t in lead["tags"]] == ["SMM"]
    assert f"№{lead['id']}" in session.sent[-1]
