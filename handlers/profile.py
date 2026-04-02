from aiogram import F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram import Router

from db.services.users_service import UserService
from keyboards.profile_menu import profile_keyboard
from texts.messages import get_profile_text

router = Router()
user_service = UserService()


@router.message(Command("profile"))
async def profile_command(message: Message):
    profile_data = await user_service.get_profile_data(message.from_user.id)

    if profile_data is None:
        await message.answer(
            "Пользователь не найден в базе данных.",
            reply_markup=profile_keyboard,
        )
        return

    await message.answer(
        get_profile_text(profile_data),
        reply_markup=profile_keyboard,
        disable_web_page_preview=True,
        parse_mode="HTML"
    )


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
        parse_mode="HTML"
    )
    await callback.answer()
