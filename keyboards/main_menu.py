from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Приступить к заданию", callback_data="start_task")],
        [
            InlineKeyboardButton(text="Личный кабинет", callback_data="profile"),
            InlineKeyboardButton(text="Доп. задания", callback_data="extra_tasks")
        ],
        [
            InlineKeyboardButton(text="Реферальная программа", callback_data="referral"),
            InlineKeyboardButton(text="Помощь", callback_data="help")
        ]
    ]
)