from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_payments_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Открыть заявки", callback_data="admin_payments:0")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_main_menu")],
        ]
    )


def get_payment_detail_keyboard(request_id: int, *, is_pending: bool) -> InlineKeyboardMarkup:
    buttons = []
    if is_pending:
        buttons.append([
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"admin_payment_approve:{request_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_payment_reject:{request_id}"),
        ])
    buttons.append([InlineKeyboardButton(text="◀️ К списку", callback_data="admin_payments:0")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
