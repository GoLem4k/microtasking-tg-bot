from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from filters.is_admin import is_admin
from keyboards.main_menu import get_main_keyboard
from texts.messages import START_TEXT

router = Router()


async def _show_main_menu(target: CallbackQuery | Message, state: FSMContext | None = None) -> None:
    user_id = target.from_user.id
    if state is not None:
        await state.clear()

    admin_flag = await is_admin(user_id)
    keyboard = get_main_keyboard(user_id, is_admin_flag=admin_flag)

    if isinstance(target, CallbackQuery):
        await target.message.edit_text(
            START_TEXT,
            reply_markup=keyboard,
            disable_web_page_preview=True,
            parse_mode="HTML"
        )
        await target.answer()
    else:
        await target.answer(
            START_TEXT,
            reply_markup=keyboard,
            disable_web_page_preview=True,
            parse_mode="HTML"
        )


@router.message(Command("menu"))
async def main_menu_command(message: Message, state: FSMContext):
    await _show_main_menu(message, state)


@router.callback_query(F.data == "main_menu")
async def main_menu_handler(callback: CallbackQuery, state: FSMContext):
    await _show_main_menu(callback, state)
