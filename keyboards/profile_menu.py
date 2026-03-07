from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

profile_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Вывести средства", callback_data="give_money_pls")],
        [InlineKeyboardButton(text="Назад в МЕНЮ", callback_data="main_manu")]
    ]
)