import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession

from config import settings, setup_logging
from bot.handlers import router


def create_bot() -> Bot:
    session = None
    if settings.bot_proxy:
        session = AiohttpSession(proxy=settings.bot_proxy)
        logging.getLogger(__name__).info(f"Telegram proxy: {settings.bot_proxy}")
    return Bot(settings.bot_token, session=session)


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Ozon AutoReply Bot")

    bot = create_bot()
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
