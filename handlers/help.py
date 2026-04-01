from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from filters.is_admin import is_admin
from keyboards.help_menu import help_keyboard, cancel_support_keyboard
from keyboards.main_menu import get_main_keyboard
from keyboards.admin.support_menu import admin_support_keyboard
from texts.messages import (
    HELP_TEXT,
    SUPPORT_PROMPT_TEXT,
    SUPPORT_REQUEST_SAVED_TEXT,
    get_admin_support_requests_text,
)
from states.support import SupportState
from db.services.users_service import UserService
from db.services.support_requests_service import SupportRequestService

router = Router()
user_service = UserService()
support_request_service = SupportRequestService()


@router.message(Command("help"))
async def help_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        HELP_TEXT,
        reply_markup=help_keyboard,
    )


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        HELP_TEXT,
        reply_markup=help_keyboard,
    )
    await callback.answer()


@router.callback_query(F.data == "help_support_start")
async def help_support_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.waiting_message)
    await callback.message.edit_text(
        SUPPORT_PROMPT_TEXT,
        reply_markup=cancel_support_keyboard,
    )
    await callback.answer()


@router.message(SupportState.waiting_message)
async def save_support_request(message: Message, state: FSMContext):
    if not message.text or not message.text.strip():
        await message.answer("Отправьте текстовое сообщение для поддержки.")
        return

    support_request = await support_request_service.create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        message_text=message.text.strip(),
    )

    admin_users = await user_service.get_admin_users()

    notify_text = (
        "Новая заявка в поддержку\n\n"
        f"ID заявки: {support_request.id}\n"
        f"Пользователь: @{message.from_user.username} | ID: {message.from_user.id}\n"
        f"Сообщение:\n{support_request.message_text}"
        if message.from_user.username
        else
        "Новая заявка в поддержку\n\n"
        f"ID заявки: {support_request.id}\n"
        f"Пользователь: ID {message.from_user.id}\n"
        f"Сообщение:\n{support_request.message_text}"
    )

    for admin in admin_users:
        try:
            await message.bot.send_message(admin.id, notify_text)
        except Exception:
            continue

    await state.clear()

    admin_flag = await is_admin(message.from_user.id)
    keyboard = get_main_keyboard(message.from_user.id, is_admin_flag=admin_flag)

    await message.answer(SUPPORT_REQUEST_SAVED_TEXT)
    await message.answer(
        "Главное меню",
        reply_markup=keyboard,
    )


