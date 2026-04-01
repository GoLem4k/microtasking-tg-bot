from __future__ import annotations

import asyncio
import os
import sys

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from db.models import SubmissionStatus, TaskStatus, UserStatus
from db.models.withdraw_request import WithdrawRequestStatus
from db.services.support_requests_service import SupportRequestService
from db.services.task_submissions_service import TaskSubmissionService
from db.services.tasks_service import TaskService
from db.services.users_service import UserService
from db.services.withdraw_requests_service import WithdrawRequestService
from filters.is_admin import is_admin
from keyboards.admin.common import build_back_keyboard, build_list_navigation
from keyboards.admin.payments import get_payment_detail_keyboard, get_payments_menu_keyboard
from keyboards.admin.performers import get_performer_detail_keyboard
from keyboards.admin.task_check import get_submission_detail_keyboard
from keyboards.admin.tasks import get_task_detail_keyboard
from states.admin import AdminBroadcastState
from texts.messages import (
    get_admin_broadcast_confirm_text,
    get_admin_payments_detail_text,
    get_admin_payments_list_text,
    get_admin_payments_overview_text,
    get_admin_performer_detail_text,
    get_admin_performers_list_text,
    get_admin_submission_detail_text,
    get_admin_submissions_list_text,
    get_admin_support_requests_text,
    get_admin_task_detail_text,
    get_admin_tasks_list_text,
)

router = Router()
user_service = UserService()
task_service = TaskService()
submission_service = TaskSubmissionService()
support_service = SupportRequestService()
withdraw_service = WithdrawRequestService()
PAGE_SIZE = 8


async def _ensure_admin(user_id: int) -> bool:
    return await is_admin(user_id)


@router.callback_query(F.data == "payments")
async def payments_overview(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    text = get_admin_payments_overview_text(
        pending_count=await withdraw_service.count_pending(),
        approved_count=await withdraw_service.count_by_status(WithdrawRequestStatus.APPROVED),
        rejected_count=await withdraw_service.count_by_status(WithdrawRequestStatus.REJECTED),
        total_count=await withdraw_service.count_all(),
    )
    await callback.message.edit_text(text, reply_markup=get_payments_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("admin_payments:"))
async def payments_list(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    offset = int(callback.data.split(":", 1)[1])
    total = await withdraw_service.count_all()
    items = await withdraw_service.get_page(limit=PAGE_SIZE, offset=offset)

    buttons = []
    for item in items:
        username = f"@{item.username}" if item.username else f"ID {item.user_id}"
        buttons.append([
            InlineKeyboardButton(
                text=f"#{item.id} | {username} | {item.amount}₽ | {item.status.value}",
                callback_data=f"admin_payment:{item.id}",
            )
        ])
    buttons.extend(
        build_list_navigation(prefix="admin_payments", offset=offset, total=total, limit=PAGE_SIZE, back_callback="payments").inline_keyboard
    )
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(get_admin_payments_list_text(items, offset=offset, total=total), reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_payment:"))
async def payment_detail(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    request_id = int(callback.data.split(":", 1)[1])
    item = await withdraw_service.get_by_id(request_id)
    if item is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    await callback.message.edit_text(
        get_admin_payments_detail_text(item),
        reply_markup=get_payment_detail_keyboard(request_id, is_pending=item.status == WithdrawRequestStatus.PENDING),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_payment_approve:"))
async def payment_approve(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    request_id = int(callback.data.split(":", 1)[1])
    item = await withdraw_service.get_by_id(request_id)
    if item is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    if item.status != WithdrawRequestStatus.PENDING:
        await callback.answer("Заявка уже обработана", show_alert=True)
        return
    user = await user_service.get_by_id(item.user_id) if item.user_id else None
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    if user.balance < item.amount:
        await callback.answer("Недостаточно средств на балансе пользователя", show_alert=True)
        return
    await user_service.change_balance(user_id=user.id, delta=-int(item.amount))
    item = await withdraw_service.approve(request_id)
    try:
        await callback.bot.send_message(user.id, f"Ваша заявка на вывод #{item.id} одобрена. Сумма: {item.amount} руб.")
    except Exception:
        pass
    await callback.message.edit_text(
        get_admin_payments_detail_text(item),
        reply_markup=get_payment_detail_keyboard(request_id, is_pending=False),
    )
    await callback.answer("Заявка одобрена")


@router.callback_query(F.data.startswith("admin_payment_reject:"))
async def payment_reject(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    request_id = int(callback.data.split(":", 1)[1])
    item = await withdraw_service.get_by_id(request_id)
    if item is None:
        await callback.answer("Заявка не найдена", show_alert=True)
        return
    if item.status != WithdrawRequestStatus.PENDING:
        await callback.answer("Заявка уже обработана", show_alert=True)
        return
    item = await withdraw_service.reject(request_id)
    if item.user_id:
        try:
            await callback.bot.send_message(item.user_id, f"Ваша заявка на вывод #{item.id} отклонена.")
        except Exception:
            pass
    await callback.message.edit_text(
        get_admin_payments_detail_text(item),
        reply_markup=get_payment_detail_keyboard(request_id, is_pending=False),
    )
    await callback.answer("Заявка отклонена")


@router.callback_query(F.data == "performers")
async def performers_root(callback: CallbackQuery):
    await performers_list_with_offset(callback, 0)


@router.callback_query(F.data.startswith("admin_performers:"))
async def performers_list(callback: CallbackQuery):
    offset = int(callback.data.split(":", 1)[1])
    await performers_list_with_offset(callback, offset)


async def performers_list_with_offset(callback: CallbackQuery, offset: int):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    total = await user_service.count_users()
    items = await user_service.get_users_page(limit=PAGE_SIZE, offset=offset)
    buttons = []
    for item in items:
        username = f"@{item.username}" if item.username else f"ID {item.id}"
        buttons.append([
            InlineKeyboardButton(
                text=f"{username} | {item.status.value} | {item.balance}₽",
                callback_data=f"admin_performer:{item.id}",
            )
        ])
    buttons.extend(build_list_navigation(prefix="admin_performers", offset=offset, total=total, limit=PAGE_SIZE).inline_keyboard)
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(get_admin_performers_list_text(items, offset=offset, total=total), reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_performer:"))
async def performer_detail(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    user_id = int(callback.data.split(":", 1)[1])
    profile_data = await user_service.get_profile_data(user_id)
    if profile_data is None:
        await callback.answer("Исполнитель не найден", show_alert=True)
        return
    status_value = profile_data.get("status").value if hasattr(profile_data.get("status"), "value") else str(profile_data.get("status"))
    await callback.message.edit_text(
        get_admin_performer_detail_text(profile_data),
        reply_markup=get_performer_detail_keyboard(user_id, is_admin=status_value == "admin"),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_performer_toggle:"))
async def performer_toggle(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    user_id = int(callback.data.split(":", 1)[1])
    user = await user_service.get_by_id(user_id)
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    new_status = UserStatus.USER if user.status == UserStatus.ADMIN else UserStatus.ADMIN
    await user_service.update(user_id, status=new_status)
    profile_data = await user_service.get_profile_data(user_id)
    await callback.message.edit_text(
        get_admin_performer_detail_text(profile_data),
        reply_markup=get_performer_detail_keyboard(user_id, is_admin=new_status == UserStatus.ADMIN),
    )
    await callback.answer("Статус изменён")


@router.callback_query(F.data == "tasks")
async def tasks_root(callback: CallbackQuery):
    await tasks_list_with_offset(callback, 0)


@router.callback_query(F.data.startswith("admin_tasks:"))
async def tasks_list(callback: CallbackQuery):
    offset = int(callback.data.split(":", 1)[1])
    await tasks_list_with_offset(callback, offset)


async def tasks_list_with_offset(callback: CallbackQuery, offset: int):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    total = await task_service.count_all()
    items = await task_service.get_page(limit=PAGE_SIZE, offset=offset)
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"#{item.id} | {item.title} | {int(item.reward)}₽ | {item.status.value}",
                callback_data=f"admin_task:{item.id}",
            )
        ])
    buttons.extend(build_list_navigation(prefix="admin_tasks", offset=offset, total=total, limit=PAGE_SIZE).inline_keyboard)
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(get_admin_tasks_list_text(items, offset=offset, total=total), reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_task:"))
async def task_detail(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id = int(callback.data.split(":", 1)[1])
    data = await task_service.get_admin_task_data(task_id)
    if data is None:
        await callback.answer("Задание не найдено", show_alert=True)
        return
    await callback.message.edit_text(
        get_admin_task_detail_text(data),
        reply_markup=get_task_detail_keyboard(task_id, status=data["status"]),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_task_activate:"))
async def task_activate(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id = int(callback.data.split(":", 1)[1])
    await task_service.set_status(task_id, TaskStatus.ACTIVE)
    data = await task_service.get_admin_task_data(task_id)
    await callback.message.edit_text(get_admin_task_detail_text(data), reply_markup=get_task_detail_keyboard(task_id, status=data["status"]))
    await callback.answer("Задание активировано")


@router.callback_query(F.data.startswith("admin_task_hide:"))
async def task_hide(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id = int(callback.data.split(":", 1)[1])
    await task_service.set_status(task_id, TaskStatus.HIDDEN)
    data = await task_service.get_admin_task_data(task_id)
    await callback.message.edit_text(get_admin_task_detail_text(data), reply_markup=get_task_detail_keyboard(task_id, status=data["status"]))
    await callback.answer("Задание скрыто")


@router.callback_query(F.data.startswith("admin_task_restart:"))
async def task_restart(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id = int(callback.data.split(":", 1)[1])
    await task_service.restart_task(task_id)
    data = await task_service.get_admin_task_data(task_id)
    await callback.message.edit_text(get_admin_task_detail_text(data), reply_markup=get_task_detail_keyboard(task_id, status=data["status"]))
    await callback.answer("Задание перезапущено")


@router.callback_query(F.data.startswith("admin_task_delete:"))
async def task_delete(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id = int(callback.data.split(":", 1)[1])
    ok = await task_service.delete(task_id)
    if not ok:
        await callback.answer("Задание не найдено", show_alert=True)
        return
    await callback.answer("Задание удалено")
    await tasks_list_with_offset(callback, 0)


@router.callback_query(F.data == "dispatch")
async def dispatch_start(callback: CallbackQuery, state: FSMContext):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await state.clear()
    await state.set_state(AdminBroadcastState.waiting_text)
    await callback.message.edit_text(
        "Рассылка\n\nОтправьте одним сообщением текст, который нужно разослать всем пользователям.",
        reply_markup=build_back_keyboard(),
    )
    await callback.answer()


@router.message(AdminBroadcastState.waiting_text)
async def dispatch_preview(message: Message, state: FSMContext):
    if not await _ensure_admin(message.from_user.id):
        return
    text = (message.text or "").strip()
    if not text:
        await message.answer("Нужен текст для рассылки.")
        return
    await state.update_data(broadcast_text=text)
    await state.set_state(AdminBroadcastState.waiting_confirm)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="admin_dispatch_send")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_main_menu")],
    ])
    await message.answer(get_admin_broadcast_confirm_text(text), reply_markup=keyboard)


@router.callback_query(F.data == "admin_dispatch_send")
async def dispatch_send(callback: CallbackQuery, state: FSMContext):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    data = await state.get_data()
    text = (data.get("broadcast_text") or "").strip()
    if not text:
        await callback.answer("Текст рассылки не найден", show_alert=True)
        return
    users = await user_service.get_all()
    success = 0
    failed = 0
    for user in users:
        try:
            await callback.bot.send_message(user.id, text)
            success += 1
        except Exception:
            failed += 1
    await state.clear()
    await callback.message.edit_text(f"Рассылка завершена.\n\nУспешно: {success}\nОшибок: {failed}", reply_markup=build_back_keyboard())
    await callback.answer()


@router.callback_query(F.data == "reboot")
async def reboot_bot(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await callback.message.edit_text("Бот перезапускается...", reply_markup=build_back_keyboard())
    await callback.answer("Перезапуск")

    async def _restart():
        await asyncio.sleep(0.7)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    asyncio.create_task(_restart())


@router.callback_query(F.data == "task_check")
async def task_check_root(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await submissions_list_with_offset(callback, 0)


@router.callback_query(F.data.startswith("admin_task_check:"))
async def task_check_list(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    offset = int(callback.data.split(":", 1)[1])
    await submissions_list_with_offset(callback, offset)


async def submissions_list_with_offset(callback: CallbackQuery, offset: int):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    total = await submission_service.count_pending()
    items = await submission_service.get_pending_page(limit=PAGE_SIZE, offset=offset)
    buttons = []
    for item in items:
        buttons.append([
            InlineKeyboardButton(
                text=f"#{item['id']} | {item['username']} | {item['task_title']}",
                callback_data=f"admin_submission:{item['id']}",
            )
        ])
    buttons.extend(build_list_navigation(prefix="admin_task_check", offset=offset, total=total, limit=PAGE_SIZE).inline_keyboard)
    markup = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(get_admin_submissions_list_text(items, offset=offset, total=total), reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_submission:"))
async def submission_detail(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    submission_id = int(callback.data.split(":", 1)[1])
    item = await submission_service.get_admin_submission_data(submission_id)
    if item is None:
        await callback.answer("Отправка не найдена", show_alert=True)
        return
    await callback.message.edit_text(
        get_admin_submission_detail_text(item),
        reply_markup=get_submission_detail_keyboard(submission_id, is_pending=item["status"] == "pending", has_screenshot=bool(item.get("screenshot_id"))),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_submission_photo:"))
async def submission_photo(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    submission_id = int(callback.data.split(":", 1)[1])
    item = await submission_service.get_admin_submission_data(submission_id)
    if item is None or not item.get("screenshot_id"):
        await callback.answer("Скриншот не найден", show_alert=True)
        return
    try:
        await callback.message.answer_photo(item["screenshot_id"], caption=f"Скриншот по заявке #{submission_id}")
    except Exception:
        await callback.answer("Не удалось отправить скриншот", show_alert=True)
        return
    await callback.answer()


@router.callback_query(F.data.startswith("admin_submission_approve:"))
async def submission_approve(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    submission_id = int(callback.data.split(":", 1)[1])
    item = await submission_service.get_admin_submission_data(submission_id)
    if item is None:
        await callback.answer("Отправка не найдена", show_alert=True)
        return
    if item["status"] != "pending":
        await callback.answer("Статус уже изменён", show_alert=True)
        return
    await submission_service.set_status(submission_id, SubmissionStatus.APPROVED)
    await user_service.change_balance_with_referrals(user_id=item["user_id"], delta=int(item["reward"]))
    try:
        await callback.bot.send_message(item["user_id"], f"Задание #{item['task_id']} подтверждено. На баланс начислено {item['reward']} руб.")
    except Exception:
        pass
    item = await submission_service.get_admin_submission_data(submission_id)
    await callback.message.edit_text(
        get_admin_submission_detail_text(item),
        reply_markup=get_submission_detail_keyboard(submission_id, is_pending=False, has_screenshot=bool(item.get("screenshot_id"))),
    )
    await callback.answer("Задание подтверждено")


@router.callback_query(F.data.startswith("admin_submission_reject:"))
async def submission_reject(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    submission_id = int(callback.data.split(":", 1)[1])
    item = await submission_service.get_admin_submission_data(submission_id)
    if item is None:
        await callback.answer("Отправка не найдена", show_alert=True)
        return
    if item["status"] != "pending":
        await callback.answer("Статус уже изменён", show_alert=True)
        return
    await submission_service.set_status(submission_id, SubmissionStatus.REJECTED)
    try:
        await callback.bot.send_message(item["user_id"], f"Задание #{item['task_id']} отклонено. Если нужна помощь, откройте раздел помощи в боте.")
    except Exception:
        pass
    item = await submission_service.get_admin_submission_data(submission_id)
    await callback.message.edit_text(
        get_admin_submission_detail_text(item),
        reply_markup=get_submission_detail_keyboard(submission_id, is_pending=False, has_screenshot=bool(item.get("screenshot_id"))),
    )
    await callback.answer("Задание отклонено")


@router.callback_query(F.data == "support")
async def admin_support(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    unseen_count = await support_service.count_unseen()
    requests = await support_service.get_recent(limit=10)
    await callback.message.edit_text(get_admin_support_requests_text(requests, unseen_count), reply_markup=build_back_keyboard())
    if unseen_count > 0:
        await support_service.mark_all_viewed()
    await callback.answer()
