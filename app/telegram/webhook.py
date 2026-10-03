import logging
import secrets
from typing import Annotated, Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import APIRouter, Header, HTTPException, Request, status

from app.core.config import BotMode, Settings
from app.telegram.bot import COMMANDS, create_bot, create_dispatcher

WEBHOOK_PATH = "/telegram/webhook"
logger = logging.getLogger(__name__)


class TelegramWebhook:
    def __init__(self, bot: Bot, dispatcher: Dispatcher, secret: str) -> None:
        self.bot = bot
        self.dispatcher = dispatcher
        self._secret = secret

    async def register(self, base_url: str) -> None:
        url = base_url.rstrip("/") + WEBHOOK_PATH
        await self.bot.set_webhook(
            url=url,
            secret_token=self._secret,
            allowed_updates=self.dispatcher.resolve_used_update_types(),
        )
        await self.bot.set_my_commands(COMMANDS)
        logger.info("Telegram webhook set to %s", url)

    async def close(self) -> None:
        await self.bot.session.close()

    def build_router(self) -> APIRouter:
        router = APIRouter(include_in_schema=False)

        @router.post(WEBHOOK_PATH)
        async def receive_update(
            request: Request,
            secret: Annotated[str, Header(alias="X-Telegram-Bot-Api-Secret-Token")] = "",
        ) -> dict[str, Any]:
            if not secrets.compare_digest(secret.encode(), self._secret.encode()):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
            update = Update.model_validate(await request.json(), context={"bot": self.bot})
            try:
                await self.dispatcher.feed_update(self.bot, update)
            except Exception:
                logger.exception("Failed to process update %s", update.update_id)
            return {"ok": True}

        return router


def create_webhook(settings: Settings) -> TelegramWebhook | None:
    if settings.bot_mode is not BotMode.WEBHOOK or not settings.bot_token:
        return None
    if not settings.webhook_base_url:
        raise RuntimeError("BOT_MODE=webhook requires WEBHOOK_BASE_URL (set automatically on Render)")
    return TelegramWebhook(create_bot(settings), create_dispatcher(settings), settings.webhook_secret)
