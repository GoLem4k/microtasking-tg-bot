from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

admin_main_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Выплаты", callback_data="payments"),
            InlineKeyboardButton(text="Исполнители", callback_data="performers")
        ],
        [
            InlineKeyboardButton(text="Задания", callback_data="tasks"),
            InlineKeyboardButton(text="Рассылки", callback_data="dispatch")
        ],
        [
            InlineKeyboardButton(text="Поддержка", callback_data="support"),
            InlineKeyboardButton(text="Перезагрузка", callback_data="reboot")
        ],
        [InlineKeyboardButton(text="Проверка заданий", callback_data="task_check")]

    ]
)