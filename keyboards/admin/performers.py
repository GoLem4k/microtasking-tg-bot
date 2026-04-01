from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_performer_detail_keyboard(user_id: int, *, is_admin: bool) -> InlineKeyboardMarkup:
    title = "Сделать user" if is_admin else "Сделать admin"
    callback = f"admin_performer_toggle:{user_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=title, callback_data=callback)],
            [InlineKeyboardButton(text="◀️ К списку", callback_data="admin_performers:0")],
        ]
    )
