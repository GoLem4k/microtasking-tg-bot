from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db.services.support_requests_service import SupportRequestService
from filters.is_admin import is_admin
from keyboards.admin.support_menu import get_support_detail_keyboard
from keyboards.help_menu import cancel_support_keyboard, help_keyboard
from keyboards.main_menu import get_main_keyboard
from states.support import SupportState
from texts.messages import (
    HELP_TEXT,
    START_TEXT,
    SUPPORT_PROMPT_TEXT,
    SUPPORT_REQUEST_SAVED_TEXT,
    get_admin_support_request_detail_text,
)
from utils.admin_alerts import send_admin_alert

router = Router()
support_request_service = SupportRequestService()


@router.message(Command("help"))
async def help_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        HELP_TEXT,
        reply_markup=help_keyboard,
        disable_web_page_preview=True,
    )


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        HELP_TEXT,
        reply_markup=help_keyboard,
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data == "help_support_start")
async def help_support_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(SupportState.waiting_message)
    await callback.message.edit_text(
        SUPPORT_PROMPT_TEXT,
        reply_markup=cancel_support_keyboard,
        disable_web_page_preview=True,
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

    detail_text = get_admin_support_request_detail_text(support_request)
    detail_keyboard = get_support_detail_keyboard(
        support_request.id,
        support_request.user_id,
        back_callback="support",
    )

    await send_admin_alert(
        message.bot,
        detail_text,
        reply_markup=detail_keyboard,
    )

    await state.clear()

    admin_flag = await is_admin(message.from_user.id)
    keyboard = get_main_keyboard(message.from_user.id, is_admin_flag=admin_flag)

    await message.answer(SUPPORT_REQUEST_SAVED_TEXT)
    await message.answer(
        START_TEXT,
        reply_markup=keyboard,
        disable_web_page_preview=True,
        parse_mode="HTML"
    )
