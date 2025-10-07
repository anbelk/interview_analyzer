import asyncio
from aiogram import Bot, Dispatcher
from src.config import BOT_TOKEN
from src.config import LOG_FILE
from src.handlers import register_handlers
from loguru import logger

logger.remove()

logger.add(
    LOG_FILE,
    rotation="10 MB",
    retention="7 days",
    compression="zip",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

logger.add(
    sink=lambda msg: print(msg, end=""),
    level="INFO",
    format="{time:HH:mm:ss} | {level} | {message}"
)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    await register_handlers(dp)
    logger.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())