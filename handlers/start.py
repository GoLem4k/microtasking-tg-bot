from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

from keyboards.main_menu import main_keyboard
from texts.messages import START_TEXT

router = Router()
@router.message(CommandStart())
async def start_handler(message: Message):

    await message.answer(
        START_TEXT,
        reply_markup=main_keyboard
    )