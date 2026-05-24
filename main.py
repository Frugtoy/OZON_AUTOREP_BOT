import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession

from config import settings, setup_logging
from bot.handlers import router


def create_bot(proxy_url: str | None = None) -> Bot:
    session = None
    if proxy_url:
        session = AiohttpSession(proxy=proxy_url)
        logging.getLogger(__name__).info(f"Telegram proxy: {proxy_url}")
    return Bot(settings.bot_token, session=session)


async def main():
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting Ozon AutoReply Bot")

    # Пробуем прокси по очереди (fallback)
    bot = None
    proxies = settings.bot_proxies
    if proxies:
        for proxy in proxies:
            try:
                bot = create_bot(proxy)
                # Тестовый запрос чтобы проверить соединение
                me = await bot.get_me()
                logger.info(f"Подключено через прокси {proxy}, бот: @{me.username}")
                break
            except Exception as e:
                logger.warning(f"Прокси {proxy} не работает: {e}")
                if bot:
                    await bot.session.close()
                bot = None
        if bot is None:
            logger.error("Все прокси недоступны, пробуем без прокси...")
            bot = create_bot(None)
    else:
        bot = create_bot(None)

    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
