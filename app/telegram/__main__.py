import asyncio
import logging

from app.core.config import BotMode, get_settings
from app.telegram.bot import COMMANDS, create_bot, create_dispatcher


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    settings = get_settings()
    if not settings.bot_token:
        raise SystemExit("BOT_TOKEN is not set")
    if settings.bot_mode is BotMode.WEBHOOK:
        raise SystemExit("BOT_MODE=webhook: the bot runs inside the web app, polling process is not needed")

    bot = create_bot(settings)
    dispatcher = create_dispatcher(settings)
    await bot.delete_webhook()
    await bot.set_my_commands(COMMANDS)
    await dispatcher.start_polling(bot, allowed_updates=dispatcher.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
