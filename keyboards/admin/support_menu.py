from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_support_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="support")],
        [InlineKeyboardButton(text="◀️ Назад в админ меню", callback_data="admin_main_menu")],
    ]
)
