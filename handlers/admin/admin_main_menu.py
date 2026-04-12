from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from db.services.support_requests_service import SupportRequestService
from db.services.task_submissions_service import TaskSubmissionService
from db.services.tasks_service import TaskService
from db.services.users_service import UserService
from db.services.withdraw_requests_service import WithdrawRequestService
from handlers.admin.admin_panel import _ensure_admin
from keyboards.admin.admin_main_menu import admin_main_keyboard
from texts.messages import get_admin_main_text

router = Router()
user_service = UserService()
task_service = TaskService()
submission_service = TaskSubmissionService()
support_service = SupportRequestService()
withdraw_service = WithdrawRequestService()


async def _get_admin_dashboard_text() -> str:
    stats = {
        "users_total": await user_service.count_users(),
        "tasks_total": await task_service.count_all(),
        "tasks_active": await task_service.count_active(),
        "pending_submissions": await submission_service.count_pending(),
        "pending_withdrawals": await withdraw_service.count_pending(),
        "new_support": await support_service.count_unseen(),
    }
    return get_admin_main_text(stats)


@router.message(Command("admin"))
async def admin_menu_command(message: Message):
    if not await _ensure_admin(message.from_user.id):
        await message.answer(
            "😐 У вас нет доступа к админ-панели.\n\n"
            "👨‍💻 Вернуться в пользовательское меню можно\n"
            "по команде: /start или /menu"
        )
        return

    await message.answer(
        await _get_admin_dashboard_text(),
        reply_markup=admin_main_keyboard,
    )

@router.callback_query(F.data == "admin_main_menu")
async def admin_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text(await _get_admin_dashboard_text(), reply_markup=admin_main_keyboard)
    await callback.answer()
