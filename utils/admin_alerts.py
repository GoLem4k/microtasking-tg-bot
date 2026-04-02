from __future__ import annotations

from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup

from config import ADMIN_ALERTS_CHAT_ID


async def send_admin_alert(
    bot: Bot,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
) -> bool:
    if ADMIN_ALERTS_CHAT_ID is None:
        return False
    try:
        await bot.send_message(
            ADMIN_ALERTS_CHAT_ID,
            text,
            reply_markup=reply_markup,
            disable_web_page_preview=True,
        )
        return True
    except Exception:
        return False
