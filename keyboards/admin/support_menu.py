from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.admin.common import build_list_navigation


def get_support_list_keyboard(requests, *, offset: int, total: int, limit: int) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for request in requests:
        username = f"@{request.username}" if request.username else f"ID {request.user_id}"
        status = "🆕" if not request.is_viewed else ""
        rows.append([
            InlineKeyboardButton(
                text=f"{status} #{request.id} | {username}",
                callback_data=f"admin_support_request:{request.id}:{offset}",
            )
        ])
    rows.extend(
        build_list_navigation(
            prefix="admin_support",
            offset=offset,
            total=total,
            limit=limit,
            back_callback="admin_main_menu",
        ).inline_keyboard
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_support_detail_keyboard(request_id: int, user_id: int | None, *, back_callback: str = "support") -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(text="Ответить", callback_data=f"admin_support_reply:{request_id}"),
            InlineKeyboardButton(text="Удалить", callback_data=f"admin_support_delete:{request_id}"),
        ]
    ]
    if user_id is not None:
        rows.append([InlineKeyboardButton(text="История запросов", callback_data=f"admin_support_history:{user_id}:0")])
    rows.append([InlineKeyboardButton(text="Назад", callback_data=back_callback)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_support_reply_cancel_keyboard(request_id: int, *, back_callback: str = "support") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data=f"admin_support_request:{request_id}:{back_callback.split(':')[-1] if back_callback.startswith('admin_support_request:') else 0}")],
            [InlineKeyboardButton(text="К списку", callback_data=back_callback)],
        ]
    )


def get_support_history_keyboard(requests, *, user_id: int, offset: int, total: int, limit: int, back_callback: str = "support") -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for request in requests:
        rows.append([
            InlineKeyboardButton(
                text=f"#{request.id} | {request.status.value}",
                callback_data=f"admin_support_history_request:{request.id}:{user_id}:{offset}",
            )
        ])
    rows.extend(
        build_list_navigation(
            prefix=f"admin_support_history:{user_id}",
            offset=offset,
            total=total,
            limit=limit,
            back_callback=back_callback,
        ).inline_keyboard
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
