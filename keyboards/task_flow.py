from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_task_rules_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я согласен и готов написать отзыв", callback_data="task_rules_accept:main")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")],
        ]
    )


def get_unfinished_task_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="▶️ Продолжить выполнение", callback_data="task_unfinished_continue")],
            [InlineKeyboardButton(text="🆕 Взять новое задание", callback_data="task_unfinished_cancel")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")],
        ]
    )


def get_city_request_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")],
        ]
    )


def get_task_platforms_keyboard(platform_buttons: list[tuple[str, str]], *, include_extra_button: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for text, callback_data in platform_buttons:
        rows.append([InlineKeyboardButton(text=text, callback_data=callback_data)])

    if include_extra_button:
        rows.append([InlineKeyboardButton(text="🧩 Доп. задания", callback_data="extra_tasks")])

    rows.append([InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)



def get_task_detail_keyboard(task_id: int, *, category: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Начать это задание", callback_data=f"task_start_selected:{task_id}")],
            [InlineKeyboardButton(text="◀️ Назад к списку", callback_data=f"task_show_list:{category}")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")],
        ]
    )



def get_no_tasks_keyboard(*, include_extra_button: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if include_extra_button:
        rows.append([InlineKeyboardButton(text="🧩 Доп. задания", callback_data="extra_tasks")])
    rows.append([InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_task_variants_keyboard(task_buttons: list[tuple[str, str]], *, category: str) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for text_value, callback_data in task_buttons:
        rows.append([InlineKeyboardButton(text=text_value, callback_data=callback_data)])

    rows.append([InlineKeyboardButton(text="◀️ Назад к платформам", callback_data=f"task_show_list:{category}")])
    rows.append([InlineKeyboardButton(text="🏠 В меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
