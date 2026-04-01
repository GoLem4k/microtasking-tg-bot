from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_task_detail_keyboard(task_id: int, *, status: str) -> InlineKeyboardMarkup:
    buttons = []
    if status != "active":
        buttons.append([InlineKeyboardButton(text="▶️ Активировать", callback_data=f"admin_task_activate:{task_id}")])
    if status != "hidden":
        buttons.append([InlineKeyboardButton(text="🙈 Скрыть", callback_data=f"admin_task_hide:{task_id}")])
    buttons.append([InlineKeyboardButton(text="🔄 Перезапустить", callback_data=f"admin_task_restart:{task_id}")])
    buttons.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_task_delete:{task_id}")])
    buttons.append([InlineKeyboardButton(text="◀️ К списку", callback_data="admin_tasks:0")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
