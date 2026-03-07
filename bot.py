import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from handlers import start, help
from handlers import main_manu, start_task, profile



async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(help.router)
    dp.include_router(main_manu.router)
    dp.include_router(start_task.router)
    dp.include_router(profile.router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())