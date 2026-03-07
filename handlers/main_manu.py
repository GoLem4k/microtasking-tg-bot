from aiogram import F
from aiogram.types import CallbackQuery
from aiogram import Router

from keyboards.main_menu import main_keyboard
from texts.messages import START_TEXT

router = Router()


@router.callback_query(F.data == "main_manu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        START_TEXT,
        reply_markup=main_keyboard
    )

    await callback.answer()
