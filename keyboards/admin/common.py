from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def build_back_keyboard(back_callback: str = "admin_main_menu") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)]],
    )


def build_list_navigation(*, prefix: str, offset: int, total: int, limit: int, back_callback: str = "admin_main_menu") -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    if offset > 0:
        prev_offset = max(offset - limit, 0)
        row.append(InlineKeyboardButton(text="⬅️", callback_data=f"{prefix}:{prev_offset}"))
    if offset + limit < total:
        next_offset = offset + limit
        row.append(InlineKeyboardButton(text="➡️", callback_data=f"{prefix}:{next_offset}"))
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
