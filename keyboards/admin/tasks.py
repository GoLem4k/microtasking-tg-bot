from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from keyboards.admin.common import build_list_navigation


CATEGORY_TITLES = {
    "all": "Все",
    "main": "Обычные",
    "extra": "Доп.",
}


def get_tasks_list_keyboard(*, items, category_key: str, offset: int, total: int, limit: int) -> InlineKeyboardMarkup:
    buttons: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="➕ Добавить обычное", callback_data="admin_task_create:main"),
            InlineKeyboardButton(text="➕ Добавить доп.", callback_data="admin_task_create:extra"),
        ],
        [
            InlineKeyboardButton(text=("• " if category_key == "all" else "") + "📚 Все", callback_data="admin_tasks:all:0"),
            InlineKeyboardButton(text=("• " if category_key == "main" else "") + "🚀 Обычные", callback_data="admin_tasks:main:0"),
            InlineKeyboardButton(text=("• " if category_key == "extra" else "") + "🧩 Доп.", callback_data="admin_tasks:extra:0"),
        ],
    ]

    for item in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"#{item.id} | {item.title} | {int(item.reward)}₽ | {item.current_completions}/{item.max_completions} | {item.status.value}",
                callback_data=f"admin_task:{item.id}:{category_key}:{offset}",
            )
        ])

    buttons.extend(
        build_list_navigation(
            prefix=f"admin_tasks:{category_key}",
            offset=offset,
            total=total,
            limit=limit,
            back_callback="admin_main_menu",
        ).inline_keyboard
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_task_detail_keyboard(task_id: int, *, status: str, category_key: str = "all", offset: int = 0) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_task_edit_menu:{task_id}:{category_key}:{offset}")],
    ]
    if status != "active":
        buttons.append([InlineKeyboardButton(text="▶️ Активировать", callback_data=f"admin_task_activate:{task_id}:{category_key}:{offset}")])
    if status != "hidden":
        buttons.append([InlineKeyboardButton(text="🙈 Скрыть", callback_data=f"admin_task_hide:{task_id}:{category_key}:{offset}")])
    buttons.append([InlineKeyboardButton(text="🔄 Перезапустить", callback_data=f"admin_task_restart:{task_id}:{category_key}:{offset}")])
    buttons.append([InlineKeyboardButton(text="🗑 Удалить", callback_data=f"admin_task_delete_confirm:{task_id}:{category_key}:{offset}")])
    buttons.append([InlineKeyboardButton(text="◀️ К списку", callback_data=f"admin_tasks:{category_key}:{offset}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_task_edit_menu_keyboard(task_id: int, *, category_key: str = "all", offset: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏷 Название", callback_data=f"admin_task_edit:{task_id}:title:{category_key}:{offset}"),
                InlineKeyboardButton(text="📝 Описание", callback_data=f"admin_task_edit:{task_id}:description:{category_key}:{offset}"),
            ],
            [
                InlineKeyboardButton(text="🔗 Инструкция", callback_data=f"admin_task_edit:{task_id}:note:{category_key}:{offset}"),
                InlineKeyboardButton(text="💰 Цена", callback_data=f"admin_task_edit:{task_id}:reward:{category_key}:{offset}"),
            ],
            [
                InlineKeyboardButton(text="📊 Лимит", callback_data=f"admin_task_edit:{task_id}:max_completions:{category_key}:{offset}"),
                InlineKeyboardButton(text="📍 Город", callback_data=f"admin_task_edit:{task_id}:city:{category_key}:{offset}"),
            ],
            [InlineKeyboardButton(text="🧷 Категория", callback_data=f"admin_task_edit_category:{task_id}:{category_key}:{offset}")],
            [InlineKeyboardButton(text="◀️ К заданию", callback_data=f"admin_task:{task_id}:{category_key}:{offset}")],
        ]
    )


def get_task_category_keyboard(task_id: int, *, category_key: str = "all", offset: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Обычное", callback_data=f"admin_task_set_category:{task_id}:main:{category_key}:{offset}"),
                InlineKeyboardButton(text="Доп.", callback_data=f"admin_task_set_category:{task_id}:extra:{category_key}:{offset}"),
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin_task_edit_menu:{task_id}:{category_key}:{offset}")],
        ]
    )


def get_task_create_cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отмена", callback_data="admin_tasks_cancel")]]
    )


def get_task_create_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Создать", callback_data="admin_task_create_confirm")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_tasks_cancel")],
        ]
    )


def get_task_delete_confirm_keyboard(task_id: int, *, category_key: str = "all", offset: int = 0) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Да, удалить", callback_data=f"admin_task_delete:{task_id}:{category_key}:{offset}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data=f"admin_task:{task_id}:{category_key}:{offset}")],
        ]
    )
