from aiogram import F, Router
from aiogram.types import CallbackQuery

from db.services.users_service import UserService
from keyboards.referral_menu import get_referral_keyboard
from texts.messages import get_referral_program_text

router = Router()
user_service = UserService()


@router.callback_query(F.data == "referral")
async def referral_program(callback: CallbackQuery):
    bot_info = await callback.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start=ref_{callback.from_user.id}"

    summary = await user_service.get_referral_summary(callback.from_user.id)

    if summary is None:
        level1_count = 0
        level2_count = 0
        level1_earnings = 0
        level2_earnings = 0
    else:
        level1_count = summary.level1_count
        level2_count = summary.level2_count
        level1_earnings = summary.level1_earnings
        level2_earnings = summary.level2_earnings

    text = get_referral_program_text(
        referral_link=referral_link,
        level1_count=level1_count,
        level2_count=level2_count,
        level1_earnings=level1_earnings,
        level2_earnings=level2_earnings,
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_referral_keyboard(referral_link),
        disable_web_page_preview=True,
    )
    await callback.answer()
