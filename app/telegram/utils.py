from aiogram.types import Message, User

from app.modules.leads.schemas import TelegramSender


def sender_from(user: User) -> TelegramSender:
    return TelegramSender(chat_id=user.id, full_name=user.full_name, username=user.username)


def message_text(message: Message) -> str:
    return message.text or message.caption or f"[{message.content_type}]"
