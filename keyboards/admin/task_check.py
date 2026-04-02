from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_submission_detail_keyboard(submission_id: int, *, is_pending: bool, has_screenshot: bool) -> InlineKeyboardMarkup:
    buttons = []
    if has_screenshot:
        buttons.append([InlineKeyboardButton(text="🖼 Скриншот", callback_data=f"admin_submission_photo:{submission_id}")])
    if is_pending:
        buttons.append([
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_submission_approve:{submission_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_submission_reject:{submission_id}"),
        ])
    buttons.append([InlineKeyboardButton(text="◀️ К списку проверок", callback_data="admin_task_check:0")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
