from urllib.parse import quote

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



def get_referral_keyboard(referral_link: str) -> InlineKeyboardMarkup:
    share_text = (
        "Присоединяйся к боту и зарабатывай вместе со мной. "
        "Вот моя реферальная ссылка:"
    )
    share_url = (
        "https://t.me/share/url?"
        f"url={quote(referral_link)}&text={quote(share_text)}"
    )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 Поделиться", url=share_url)],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="main_menu")],
        ]
    )
