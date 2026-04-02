from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db.models import TaskCategory
from handlers.start_task import begin_city_request, cleanup_expired_submissions, show_tasks_for_category, show_unfinished_warning_if_needed
from db.services.users_service import UserService

router = Router()
user_service = UserService()


@router.message(Command("extra"))
async def extra_tasks_command(message: Message, state: FSMContext):
    await state.clear()
    await cleanup_expired_submissions(message.from_user.id)

    user = await user_service.get_by_id(message.from_user.id)
    if user is not None and user.city_id is not None:
        await show_tasks_for_category(message, user_id=message.from_user.id, category=TaskCategory.EXTRA)
        return

    await begin_city_request(message, state, category=TaskCategory.EXTRA)


@router.callback_query(F.data == "extra_tasks")
async def extra_tasks(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await cleanup_expired_submissions(callback.from_user.id)

    if await show_unfinished_warning_if_needed(callback):
        return

    user = await user_service.get_by_id(callback.from_user.id)
    if user is not None and user.city_id is not None:
        await show_tasks_for_category(callback, user_id=callback.from_user.id, category=TaskCategory.EXTRA)
        return

    await begin_city_request(callback, state, category=TaskCategory.EXTRA)
