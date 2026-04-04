from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_performer_detail_keyboard(user_id: int, *, status_value: str) -> InlineKeyboardMarkup:
    rows = []

    if status_value == "ban":
        rows.append([InlineKeyboardButton(text="✅ Разблокировать", callback_data=f"admin_performer_unban:{user_id}")])
    else:
        rows.append([InlineKeyboardButton(text="⛔️ Заблокировать", callback_data=f"admin_performer_ban:{user_id}")])
        rows.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_performer_delete:{user_id}")])
        toggle_title = "👤 Сделать user" if status_value == "admin" else "⭐️ Сделать admin"
        rows.append([InlineKeyboardButton(text=toggle_title, callback_data=f"admin_performer_toggle:{user_id}")])

    rows.append([InlineKeyboardButton(text="◀️ К списку исполнителей", callback_data="admin_performers:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
