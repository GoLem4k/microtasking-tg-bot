from aiogram import F
from aiogram.types import CallbackQuery
from aiogram import Router

from db.services.users_service import UserService
from keyboards.profile_menu import profile_keyboard
from texts.messages import get_profile_text

router = Router()
user_service = UserService()


@router.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    profile_data = await user_service.get_profile_data(callback.from_user.id)

    if profile_data is None:
        await callback.message.edit_text(
            "Пользователь не найден в базе данных.",
            reply_markup=profile_keyboard,
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        get_profile_text(profile_data),
        reply_markup=profile_keyboard,
        disable_web_page_preview=True,
    )
    await callback.answer()
