import asyncio
from aiogram import Bot, Dispatcher

from app.config import settings
from app.middlewares.auth import AuthMiddleware
from app.handlers import start, apartments, sets
from app.notifications.scheduler import setup_scheduler

from app.database.db import engine
from app.database.models import Base


async def main():
    # Создание таблиц в БД (если их еще нет)
    async with engine.begin() as conn:
        # создание таблиц в БД с использованием SQLAlchemy
        await conn.run_sync(Base.metadata.create_all)
    
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    scheduler = setup_scheduler(bot)
    scheduler.start()

    dp.message.middleware(AuthMiddleware(settings.admins))

    dp.include_router(start.router)
    dp.include_router(apartments.router)
    dp.include_router(sets.router)
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())