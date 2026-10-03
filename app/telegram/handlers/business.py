import logging

from aiogram import Bot, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BusinessConnection, Message

from app.modules.leads.service import LeadService
from app.telegram.utils import message_text, sender_from

logger = logging.getLogger(__name__)


async def on_connection(connection: BusinessConnection, bot: Bot) -> None:
    logger.info("Business connection %s enabled=%s", connection.id, connection.is_enabled)
    text = (
        "✅ Telegram подключён к CRM: входящие сообщения клиентов будут появляться как лиды."
        if connection.is_enabled
        else "Telegram отключён от CRM."
    )
    try:
        await bot.send_message(connection.user_chat_id, text)
    except TelegramAPIError:
        logger.warning("Cannot notify the owner of business connection %s", connection.id)


async def on_incoming_message(message: Message, lead_service: LeadService) -> None:
    sender = message.from_user
    if sender is None or sender.is_bot or sender.id != message.chat.id:
        return
    lead = await lead_service.register_incoming_message(sender_from(sender), message_text(message))
    logger.info("Business message from %s stored in lead %s", sender.id, lead.id)


def create_router() -> Router:
    router = Router(name="business")
    router.business_connection.register(on_connection)
    router.business_message.register(on_incoming_message)
    return router
