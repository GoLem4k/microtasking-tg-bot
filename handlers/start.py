from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from keyboards.main_menu import get_main_keyboard  # <- используем функцию
from texts.messages import START_TEXT

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id  # реальный Telegram ID
    keyboard = get_main_keyboard(user_id)  # клавиатура с проверкой админа

    await message.answer(
        START_TEXT,
        reply_markup=keyboard
    )