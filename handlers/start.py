from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from filters.is_admin import is_admin
from filters.is_new_user import is_new_user
from keyboards.main_menu import get_main_keyboard
from texts.messages import START_TEXT

router = Router()



def extract_ref_parent_id(message_text: str | None) -> int | None:
    if not message_text:
        return None

    parts = message_text.split(maxsplit=1)
    if len(parts) < 2:
        return None

    start_arg = parts[1].strip()
    if not start_arg.startswith("ref_"):
        return None

    ref_value = start_arg.removeprefix("ref_").strip()
    if not ref_value.isdigit():
        return None

    return int(ref_value)


@router.message(CommandStart())
async def start_handler(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username
    ref_parent_id = extract_ref_parent_id(message.text)

    if ref_parent_id == user_id:
        ref_parent_id = None

    await is_new_user(user_id, username, ref_parent_id=ref_parent_id)

    admin_flag = await is_admin(user_id)
    keyboard = get_main_keyboard(user_id, is_admin_flag=admin_flag)

    await message.answer(
        START_TEXT,
        reply_markup=keyboard,
        disable_web_page_preview=True,
        parse_mode="HTML"
    )
