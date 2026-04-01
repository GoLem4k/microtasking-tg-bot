from aiogram import F, Router
from aiogram.types import CallbackQuery

from filters.is_admin import is_admin
from keyboards.main_menu import get_main_keyboard
from texts.messages import START_TEXT

router = Router()

@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery):
    user_id = callback.from_user.id

    admin_flag = await is_admin(user_id)
    keyboard = get_main_keyboard(user_id, is_admin_flag=admin_flag)

    await callback.message.edit_text(
        START_TEXT,
        reply_markup=keyboard
    )
    await callback.answer()