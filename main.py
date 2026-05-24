import asyncio
import logging
from typing import Optional

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.session.aiohttp import AiohttpSession

from config import settings, setup_logging
from bot.handlers import router

logger = logging.getLogger(__name__)


def create_bot(proxy_url: Optional[str] = None) -> Optional[Bot]:
    """Создаёт бота с опциональным прокси и увеличенным таймаутом."""
    session: Optional[AiohttpSession] = None
    if proxy_url:
        try:
            session = AiohttpSession(proxy=proxy_url)
            logger.info(f"Proxy configured: {proxy_url}")
        except RuntimeError as exc:
            logger.warning(f"Proxy setup failed for {proxy_url}: {exc}")
            return None
    return Bot(
        settings.bot_token,
        session=session,
        request_timeout=20,  # быстрее fail → быстрее fallback
    )


async def test_connection(bot: Bot) -> bool:
    """Тестовый get_me с обязательным закрытием сессии при неудаче."""
    try:
        me = await bot.get_me()
        logger.info(f"Connected as @{me.username}")
        return True
    except Exception as exc:
        logger.warning(f"Connection test failed: {type(exc).__name__}: {exc}")
        try:
            await bot.session.close()
        except Exception:
            pass
        return False


async def main() -> None:
    setup_logging()
    logger.info("Starting Ozon AutoReply Bot v%s", "0.2.1-debug")

    bot: Optional[Bot] = None
    proxies = settings.bot_proxies

    # ── Fallback через прокси ──────────────────────────
    if proxies:
        for proxy in proxies:
            bot = create_bot(proxy)
            if bot is None:
                continue
            if await test_connection(bot):
                break
            bot = None
        if bot is None:
            logger.error("All proxies failed — trying direct connection...")

    # ── Прямое соединение (или fallback) ───────────────
    if bot is None:
        bot = create_bot(None)
        if bot is None or not await test_connection(bot):
            logger.critical(
                "Cannot connect to Telegram API. "
                "Check network, firewall, or proxy settings."
            )
            return

    # ── Dispatcher ─────────────────────────────────────
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    # close_bot_session=True по умолчанию — не закрываем вручную в finally
    await dp.start_polling(
        bot,
        skip_updates=True,
        polling_timeout=30,
    )


if __name__ == "__main__":
    asyncio.run(main())
