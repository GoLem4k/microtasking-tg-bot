from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from config import FAQ_URL, CHANNEL_URL, REVIEWS_URL, CHAT_URL


help_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📄 FAQ", url=FAQ_URL)],
        [
            InlineKeyboardButton(text="📝 Канал", url=CHANNEL_URL),
            InlineKeyboardButton(text="💬 Чат", url=CHAT_URL),
        ],
        [
            InlineKeyboardButton(text="🪢 Отзывы", url=REVIEWS_URL),
            InlineKeyboardButton(text="🤝 Поддержка", callback_data="help_support_start"),
        ],
        [InlineKeyboardButton(text="◀️ Назад в меню", callback_data="main_menu")],
    ]
)

cancel_support_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад в помощь", callback_data="help")],
        [InlineKeyboardButton(text="🏠 Назад в меню", callback_data="main_menu")],
    ]
)
