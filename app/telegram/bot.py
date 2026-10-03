from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand

from app.core.config import Settings
from app.telegram.handlers import build_router
from app.telegram.middlewares import LeadServiceMiddleware

COMMANDS = [
    BotCommand(command="start", description="Оставить заявку"),
    BotCommand(command="cancel", description="Отменить заявку"),
]


def create_bot(settings: Settings) -> Bot:
    return Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))


def create_dispatcher(settings: Settings) -> Dispatcher:
    dispatcher = Dispatcher(storage=MemoryStorage(), services=settings.bot_services)
    dispatcher.update.outer_middleware(LeadServiceMiddleware())
    dispatcher.include_router(build_router())
    return dispatcher
