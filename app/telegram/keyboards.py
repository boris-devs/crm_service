from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

NEW_APPLICATION = "📝 Оставить заявку"
SHARE_PHONE = "📱 Отправить номер"
USE_TELEGRAM = "💬 Пишите в Telegram"


class ServiceCallback(CallbackData, prefix="svc"):
    index: int


def _reply(*rows: list[KeyboardButton]) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=list(rows), resize_keyboard=True, one_time_keyboard=True)


def name_keyboard(full_name: str) -> ReplyKeyboardMarkup:
    return _reply([KeyboardButton(text=full_name)])


def contact_keyboard() -> ReplyKeyboardMarkup:
    return _reply(
        [KeyboardButton(text=SHARE_PHONE, request_contact=True)],
        [KeyboardButton(text=USE_TELEGRAM)],
    )


def restart_keyboard() -> ReplyKeyboardMarkup:
    return _reply([KeyboardButton(text=NEW_APPLICATION)])


def services_keyboard(services: list[str]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for index, service in enumerate(services):
        builder.button(text=service, callback_data=ServiceCallback(index=index))
    builder.adjust(2)
    return builder.as_markup()
