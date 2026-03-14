from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from keyboards.admin.admin_main_menu import admin_main_keyboard
from texts.messages import START_TEXT

router = Router()

@router.message(Command("admin"))
async def admin_menu_command(message: Message):
    await message.answer(
        START_TEXT,
        reply_markup=admin_main_keyboard
    )

@router.callback_query(F.data == "admin_main_menu")
async def admin_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        START_TEXT,
        reply_markup=admin_main_keyboard
    )
    await callback.answer()  # убирает "часики" на кнопке