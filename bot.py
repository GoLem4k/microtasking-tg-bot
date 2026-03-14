# bot.py
# ----------------------
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

# Импорт роутеров
from handlers import main_manu, start_task, profile, help
from handlers.admin import admin_main_menu

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # регистрация роутеров
    dp.include_router(main_manu.router)
    dp.include_router(start_task.router)
    dp.include_router(profile.router)
    dp.include_router(help.router)
    dp.include_router(admin_main_menu.router)  # админский роутер

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())