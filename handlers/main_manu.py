# handlers/main_manu.py
# ----------------------
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

# Импортируем функцию, а не переменную
from keyboards.main_menu import get_main_keyboard
from texts.messages import START_TEXT

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id  # реальный Telegram ID
    keyboard = get_main_keyboard(user_id)  # формируем клавиатуру для пользователя
    await message.answer(
        START_TEXT,
        reply_markup=keyboard
    )