from aiogram import F
from aiogram.types import CallbackQuery
from aiogram import Router

from keyboards.profile_menu import profile_keyboard
from texts.messages import PROFILE_TEXT

router = Router()

@router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    await callback.message.edit_text(
        PROFILE_TEXT,
        reply_markup=profile_keyboard
    )
    await callback.answer()