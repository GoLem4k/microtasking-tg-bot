import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN

from handlers import main_menu, start_task, profile, help, start, referral
from handlers.admin import admin_main_menu, admin_panel
from handlers.withdraw import router as withdraw_router


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(start.router)
    dp.include_router(main_menu.router)
    dp.include_router(start_task.router)
    dp.include_router(profile.router)
    dp.include_router(referral.router)
    dp.include_router(help.router)
    dp.include_router(admin_main_menu.router)
    dp.include_router(admin_panel.router)
    dp.include_router(withdraw_router)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())