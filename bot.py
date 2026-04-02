import asyncio

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import BOT_TOKEN
from handlers import extra_tasks, help, main_menu, profile, referral, start, start_task
from handlers.admin import admin_main_menu, admin_panel
from handlers.withdraw import router as withdraw_router
from middlewares.block_banned_users import BlockBannedUsersMiddleware


async def setup_bot_commands(bot: Bot) -> None:
    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Открыть главное меню"),
            BotCommand(command="menu", description="Показать главное меню"),
            BotCommand(command="task", description="Приступить к заданию"),
            BotCommand(command="extra", description="Открыть доп. задания"),
            BotCommand(command="profile", description="Личный кабинет"),
            BotCommand(command="referral", description="Реферальная программа"),
            BotCommand(command="help", description="Помощь и поддержка"),
        ]
    )


async def main():
    bot = Bot(token=BOT_TOKEN)
    await setup_bot_commands(bot)
    dp = Dispatcher()

    banned_middleware = BlockBannedUsersMiddleware()
    dp.message.outer_middleware(banned_middleware)
    dp.callback_query.outer_middleware(banned_middleware)

    dp.include_router(start.router)
    dp.include_router(main_menu.router)
    dp.include_router(start_task.router)
    dp.include_router(extra_tasks.router)
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
