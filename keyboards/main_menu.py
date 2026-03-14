# keyboards/main_menu.py
# ----------------------
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from filters.is_admin import is_admin

def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
   
    buttons = [
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

    if is_admin(user_id):  # проверка с реальным ID
        buttons.append([InlineKeyboardButton(text="⚙️ Админ меню", callback_data="admin_main_menu")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)