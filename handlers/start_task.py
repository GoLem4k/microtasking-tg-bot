from aiogram import F
from aiogram.types import CallbackQuery
from aiogram import Router

router = Router()

@router.callback_query(F.data == "start_task")
async def start_task(callback: CallbackQuery):
    await callback.message.edit_text("Начинаем задание 🚀")
    await callback.answer()