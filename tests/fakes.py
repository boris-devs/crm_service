from datetime import UTC, datetime
from itertools import count

from aiogram import Bot
from aiogram.client.session.base import BaseSession
from aiogram.methods import TelegramMethod
from aiogram.types import Chat, Message

ids = count(1)


class FakeSession(BaseSession):
    def __init__(self) -> None:
        super().__init__()
        self.methods: list[TelegramMethod] = []
        self.sent: list[str] = []

    async def make_request(self, bot: Bot, method: TelegramMethod, timeout: int | None = None):
        self.methods.append(method)
        text = getattr(method, "text", None)
        if text:
            self.sent.append(text)
        if method.__returning__ is bool:
            return True
        chat = Chat(id=getattr(method, "chat_id", 0) or 0, type="private")
        return Message(message_id=next(ids), date=datetime.now(UTC), chat=chat, text=text)

    async def close(self) -> None:
        pass

    async def stream_content(self, *args, **kwargs):
        raise NotImplementedError
