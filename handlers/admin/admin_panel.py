from __future__ import annotations

import asyncio
import os
import sys
from decimal import Decimal, InvalidOperation

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from db.models import SubmissionStatus, TaskCategory, TaskStatus, UserStatus
from db.models.withdraw_request import WithdrawRequestStatus
from db.services.cities_service import CityService
from db.services.support_requests_service import SupportRequestService
from db.services.task_submissions_service import TaskSubmissionService
from db.services.tasks_service import TaskService
from db.services.users_service import UserService
from db.services.withdraw_requests_service import WithdrawRequestService
from filters.is_admin import is_admin
from keyboards.admin.common import build_back_keyboard, build_list_navigation
from keyboards.admin.payments import get_payment_detail_keyboard, get_payments_menu_keyboard
from keyboards.admin.performers import get_performer_detail_keyboard
from keyboards.admin.support_menu import (
    get_support_detail_keyboard,
    get_support_history_keyboard,
    get_support_list_keyboard,
)
from keyboards.admin.task_check import get_submission_detail_keyboard
from keyboards.admin.tasks import (
    CATEGORY_TITLES,
    get_task_category_keyboard,
    get_task_create_cancel_keyboard,
    get_task_create_confirm_keyboard,
    get_task_delete_confirm_keyboard,
    get_task_detail_keyboard,
    get_task_edit_menu_keyboard,
    get_tasks_list_keyboard,
)
from states.admin import AdminBroadcastState, AdminSupportReplyState, AdminTaskCreateState, AdminTaskEditState
from texts.messages import (
    get_admin_broadcast_confirm_text,
    get_admin_payments_detail_text,
    get_admin_payments_list_text,
    get_admin_payments_overview_text,
    get_admin_performer_detail_text,
    get_admin_performers_list_text,
    get_admin_submission_detail_text,
    get_admin_submissions_list_text,
    get_admin_support_history_text,
    get_admin_support_request_detail_text,
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
city_service = CityService()
PAGE_SIZE = 8


async def _ensure_admin(user_id: int) -> bool:
    return await is_admin(user_id)


def _category_from_key(category_key: str) -> TaskCategory | None:
    if category_key == "main":
        return TaskCategory.MAIN
    if category_key == "extra":
        return TaskCategory.EXTRA
    return None


def _category_title(category_key: str) -> str:
    return CATEGORY_TITLES.get(category_key, "Все")


def _parse_tasks_list_callback(data: str) -> tuple[str, int]:
    parts = data.split(":")
    if len(parts) >= 3:
        return parts[1], int(parts[2])
    if len(parts) >= 2:
        return "all", int(parts[1])
    return "all", 0


def _parse_task_context(data: str, prefix: str) -> tuple[int, str, int]:
    parts = data.split(":")
    task_id = int(parts[1])
    if len(parts) >= 4:
        return task_id, parts[2], int(parts[3])
    return task_id, "all", 0


def _parse_task_edit_context(data: str) -> tuple[int, str, str, int]:
    parts = data.split(":")
    task_id = int(parts[1])
    field_name = parts[2]
    if len(parts) >= 5:
        return task_id, field_name, parts[3], int(parts[4])
    return task_id, field_name, "all", 0


def _clean_optional_text(value: str) -> str | None:
    text = value.strip()
    if not text or text == "-":
        return None
    return text


def _parse_decimal(text: str) -> Decimal:
    normalized = text.replace(",", ".").strip()
    try:
        value = Decimal(normalized)
    except InvalidOperation as exc:
        raise ValueError("Введите корректную сумму. Пример: 150 или 150.50") from exc
    if value < 0:
        raise ValueError("Сумма не может быть отрицательной")
    return value


def _parse_positive_int(text: str) -> int:
    try:
        value = int(text.strip())
    except ValueError as exc:
        raise ValueError("Введите целое число") from exc
    if value <= 0:
        raise ValueError("Значение должно быть больше 0")
    return value


def _build_task_creation_preview(data: dict) -> str:
    category = _category_title(data.get("category_key", "all"))
    description = data.get("description") or "-"
    note = data.get("note") or "-"
    city_name = data.get("city_name") or "-"
    reward = data.get("reward") or 0
    max_completions = data.get("max_completions") or 0
    return (
        "Создание задания\n\n"
        f"Категория: {category}\n"
        f"Площадка / кнопка: {data.get('title') or '-'}\n"
        f"Название / объект: {description}\n"
        f"Инструкция / примечание: {note}\n"
        f"Цена: {reward} руб.\n"
        f"Лимит выполнений: {max_completions}\n"
        f"Город: {city_name}\n\n"
        "Проверьте данные и нажмите «Создать»."
    )


def _get_edit_prompt(task_id: int, field_name: str, category_key: str, offset: int) -> tuple[str, InlineKeyboardMarkup]:
    prompts = {
        "title": "Введите новое название площадки / кнопки.\nПример: Яндекс.Карты",
        "description": "Введите новое название задания / объекта.\nОтправьте «-», чтобы очистить поле.",
        "note": "Введите новую ссылку на инструкцию или примечание.\nОтправьте «-», чтобы очистить поле.",
        "reward": "Введите новую цену задания в рублях.\nПример: 200",
        "max_completions": "Введите новый лимит выполнений.\nПример: 50",
        "city": "Введите новый город.\nОтправьте «-», чтобы сделать задание без привязки к городу.",
    }
    return prompts[field_name], build_back_keyboard(f"admin_task:{task_id}:{category_key}:{offset}")


async def _render_task_detail(message: Message, *, task_id: int, category_key: str = "all", offset: int = 0):
    data = await task_service.get_admin_task_data(task_id)
    if data is None:
        await message.edit_text("Задание не найдено", reply_markup=build_back_keyboard(f"admin_tasks:{category_key}:{offset}"))
        return
    await message.edit_text(
        get_admin_task_detail_text(data),
        reply_markup=get_task_detail_keyboard(task_id, status=data["status"], category_key=category_key, offset=offset),
    )


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
        if await user_service.can_receive_bot_messages(user.id):
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
            if await user_service.can_receive_bot_messages(item.user_id):
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
        reply_markup=get_performer_detail_keyboard(user_id, status_value=status_value),
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
    if user.status == UserStatus.BAN:
        await callback.answer("Сначала разблокируйте пользователя", show_alert=True)
        return
    new_status = UserStatus.USER if user.status == UserStatus.ADMIN else UserStatus.ADMIN
    await user_service.update(user_id, status=new_status)
    profile_data = await user_service.get_profile_data(user_id)
    await callback.message.edit_text(
        get_admin_performer_detail_text(profile_data),
        reply_markup=get_performer_detail_keyboard(user_id, status_value=new_status.value),
    )
    await callback.answer("Статус изменён")


@router.callback_query(F.data.startswith("admin_performer_ban:"))
async def performer_ban(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    user_id = int(callback.data.split(":", 1)[1])
    if user_id == callback.from_user.id:
        await callback.answer("Нельзя заблокировать самого себя", show_alert=True)
        return
    user = await user_service.get_by_id(user_id)
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    if user.status == UserStatus.BAN:
        await callback.answer("Пользователь уже заблокирован", show_alert=True)
        return
    await user_service.update(user_id, status=UserStatus.BAN)
    profile_data = await user_service.get_profile_data(user_id)
    await callback.message.edit_text(
        get_admin_performer_detail_text(profile_data),
        reply_markup=get_performer_detail_keyboard(user_id, status_value=UserStatus.BAN.value),
    )
    await callback.answer("Пользователь заблокирован")


@router.callback_query(F.data.startswith("admin_performer_unban:"))
async def performer_unban(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    user_id = int(callback.data.split(":", 1)[1])
    user = await user_service.get_by_id(user_id)
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return
    if user.status != UserStatus.BAN:
        await callback.answer("Пользователь не заблокирован", show_alert=True)
        return
    await user_service.update(user_id, status=UserStatus.USER)
    profile_data = await user_service.get_profile_data(user_id)
    await callback.message.edit_text(
        get_admin_performer_detail_text(profile_data),
        reply_markup=get_performer_detail_keyboard(user_id, status_value=UserStatus.USER.value),
    )
    await callback.answer("Пользователь разблокирован")


@router.callback_query(F.data == "tasks")
async def tasks_root(callback: CallbackQuery):
    await tasks_list_with_context(callback, "all", 0)


@router.callback_query(F.data.startswith("admin_tasks:"))
async def tasks_list(callback: CallbackQuery):
    category_key, offset = _parse_tasks_list_callback(callback.data)
    await tasks_list_with_context(callback, category_key, offset)


async def tasks_list_with_context(callback: CallbackQuery, category_key: str, offset: int):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    category = _category_from_key(category_key)
    total = await task_service.count_filtered(category=category)
    items = await task_service.get_page_filtered(category=category, limit=PAGE_SIZE, offset=offset)
    markup = get_tasks_list_keyboard(items=items, category_key=category_key, offset=offset, total=total, limit=PAGE_SIZE)
    await callback.message.edit_text(
        get_admin_tasks_list_text(items, offset=offset, total=total, category_label=_category_title(category_key)),
        reply_markup=markup,
    )
    await callback.answer()


@router.callback_query(F.data.in_({"admin_task_create:main", "admin_task_create:extra"}))
async def task_create_start(callback: CallbackQuery, state: FSMContext):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    category_key = callback.data.split(":", 1)[1]
    await state.clear()
    await state.update_data(category_key=category_key)
    await state.set_state(AdminTaskCreateState.waiting_title)
    await callback.message.edit_text(
        f"Создание задания\n\nКатегория: {_category_title(category_key)}\n\nВведите название площадки / кнопки.",
        reply_markup=get_task_create_cancel_keyboard(),
    )
    await callback.answer()


@router.message(AdminTaskCreateState.waiting_title)
async def task_create_title(message: Message, state: FSMContext):
    if not await _ensure_admin(message.from_user.id):
        return
    title = (message.text or "").strip()
    if not title:
        await message.answer("Название не может быть пустым.")
        return
    await state.update_data(title=title)
    await state.set_state(AdminTaskCreateState.waiting_description)
    await message.answer(
        "Введите название задания / объекта.\nОтправьте «-», если поле не нужно.",
        reply_markup=get_task_create_cancel_keyboard(),
    )


@router.message(AdminTaskCreateState.waiting_description)
async def task_create_description(message: Message, state: FSMContext):
    if not await _ensure_admin(message.from_user.id):
        return
    await state.update_data(description=_clean_optional_text(message.text or ""))
    await state.set_state(AdminTaskCreateState.waiting_note)
    await message.answer(
        "Введите ссылку на инструкцию или примечание.\nОтправьте «-», если поле не нужно.",
        reply_markup=get_task_create_cancel_keyboard(),
    )


@router.message(AdminTaskCreateState.waiting_note)
async def task_create_note(message: Message, state: FSMContext):
    if not await _ensure_admin(message.from_user.id):
        return
    await state.update_data(note=_clean_optional_text(message.text or ""))
    await state.set_state(AdminTaskCreateState.waiting_reward)
    await message.answer("Введите цену задания в рублях.\nПример: 200", reply_markup=get_task_create_cancel_keyboard())


@router.message(AdminTaskCreateState.waiting_reward)
async def task_create_reward(message: Message, state: FSMContext):
    if not await _ensure_admin(message.from_user.id):
        return
    try:
        reward = _parse_decimal(message.text or "")
    except ValueError as exc:
        await message.answer(str(exc))
        return
    await state.update_data(reward=str(reward))
    await state.set_state(AdminTaskCreateState.waiting_max_completions)
    await message.answer("Введите лимит выполнений.\nПример: 30", reply_markup=get_task_create_cancel_keyboard())


@router.message(AdminTaskCreateState.waiting_max_completions)
async def task_create_max_completions(message: Message, state: FSMContext):
    if not await _ensure_admin(message.from_user.id):
        return
    try:
        max_completions = _parse_positive_int(message.text or "")
    except ValueError as exc:
        await message.answer(str(exc))
        return
    await state.update_data(max_completions=max_completions)
    await state.set_state(AdminTaskCreateState.waiting_city)
    await message.answer(
        "Введите город.\nОтправьте «-», если задание без привязки к городу.",
        reply_markup=get_task_create_cancel_keyboard(),
    )


@router.message(AdminTaskCreateState.waiting_city)
async def task_create_city(message: Message, state: FSMContext):
    if not await _ensure_admin(message.from_user.id):
        return
    city_name = _clean_optional_text(message.text or "")
    await state.update_data(city_name=city_name)
    data = await state.get_data()
    await state.set_state(AdminTaskCreateState.waiting_confirm)
    await message.answer(_build_task_creation_preview(data), reply_markup=get_task_create_confirm_keyboard())


@router.callback_query(F.data == "admin_task_create_confirm")
async def task_create_confirm(callback: CallbackQuery, state: FSMContext):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    data = await state.get_data()
    if not data.get("title"):
        await callback.answer("Данные для создания задания не найдены", show_alert=True)
        return
    city_id = None
    if data.get("city_name"):
        city = await city_service.create(data["city_name"])
        city_id = city.id
    category_key = data.get("category_key", "main")
    category = _category_from_key(category_key) or TaskCategory.MAIN
    task = await task_service.create(
        title=data["title"],
        description=data.get("description"),
        note=data.get("note"),
        reward=Decimal(data.get("reward") or "0"),
        max_completions=int(data.get("max_completions") or 1),
        city_id=city_id,
        category=category,
        status=TaskStatus.ACTIVE,
    )
    await state.clear()
    await _render_task_detail(callback.message, task_id=task.id, category_key=category_key, offset=0)
    await callback.answer("Задание создано")


@router.callback_query(F.data == "admin_tasks_cancel")
async def admin_tasks_cancel(callback: CallbackQuery, state: FSMContext):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    data = await state.get_data()
    await state.clear()
    category_key = data.get("category_key", "all")
    offset = int(data.get("offset", 0) or 0)
    await tasks_list_with_context(callback, category_key, offset)


@router.callback_query(F.data.startswith("admin_task:"))
async def task_detail(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id, category_key, offset = _parse_task_context(callback.data, "admin_task")
    await _render_task_detail(callback.message, task_id=task_id, category_key=category_key, offset=offset)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_task_edit_menu:"))
async def task_edit_menu(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id, category_key, offset = _parse_task_context(callback.data, "admin_task_edit_menu")
    data = await task_service.get_admin_task_data(task_id)
    if data is None:
        await callback.answer("Задание не найдено", show_alert=True)
        return
    await callback.message.edit_text(
        get_admin_task_detail_text(data) + "\n\nЧто изменить?",
        reply_markup=get_task_edit_menu_keyboard(task_id, category_key=category_key, offset=offset),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_task_edit_category:"))
async def task_edit_category_menu(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id, category_key, offset = _parse_task_context(callback.data, "admin_task_edit_category")
    await callback.message.edit_text(
        f"Задание #{task_id}\n\nВыберите новую категорию:",
        reply_markup=get_task_category_keyboard(task_id, category_key=category_key, offset=offset),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_task_set_category:"))
async def task_set_category(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    parts = callback.data.split(":")
    task_id = int(parts[1])
    new_category_key = parts[2]
    category_key = parts[3] if len(parts) > 3 else "all"
    offset = int(parts[4]) if len(parts) > 4 else 0
    category = _category_from_key(new_category_key)
    if category is None:
        await callback.answer("Неизвестная категория", show_alert=True)
        return
    task = await task_service.update(task_id, category=category)
    if task is None:
        await callback.answer("Задание не найдено", show_alert=True)
        return
    await _render_task_detail(callback.message, task_id=task_id, category_key=category_key, offset=offset)
    await callback.answer("Категория обновлена")


@router.callback_query(F.data.startswith("admin_task_edit:"))
async def task_edit_field(callback: CallbackQuery, state: FSMContext):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id, field_name, category_key, offset = _parse_task_edit_context(callback.data)
    data = await task_service.get_admin_task_data(task_id)
    if data is None:
        await callback.answer("Задание не найдено", show_alert=True)
        return
    prompt_text, markup = _get_edit_prompt(task_id, field_name, category_key, offset)
    await state.clear()
    await state.update_data(task_id=task_id, field_name=field_name, category_key=category_key, offset=offset)
    await state.set_state(AdminTaskEditState.waiting_value)
    await callback.message.edit_text(prompt_text, reply_markup=markup)
    await callback.answer()


@router.message(AdminTaskEditState.waiting_value)
async def task_edit_value(message: Message, state: FSMContext):
    if not await _ensure_admin(message.from_user.id):
        return
    data = await state.get_data()
    task_id = int(data["task_id"])
    field_name = data["field_name"]
    category_key = data.get("category_key", "all")
    offset = int(data.get("offset", 0) or 0)
    task = await task_service.get_by_id(task_id)
    if task is None:
        await state.clear()
        await message.answer("Задание не найдено")
        return

    try:
        if field_name == "title":
            value = (message.text or "").strip()
            if not value:
                raise ValueError("Название не может быть пустым")
            await task_service.update(task_id, title=value)
        elif field_name == "description":
            await task_service.update(task_id, description=_clean_optional_text(message.text or ""))
        elif field_name == "note":
            await task_service.update(task_id, note=_clean_optional_text(message.text or ""))
        elif field_name == "reward":
            await task_service.update(task_id, reward=_parse_decimal(message.text or ""))
        elif field_name == "max_completions":
            value = _parse_positive_int(message.text or "")
            if value < task.current_completions:
                raise ValueError(f"Лимит не может быть меньше текущих выполнений: {task.current_completions}")
            await task_service.update(task_id, max_completions=value)
        elif field_name == "city":
            city_name = _clean_optional_text(message.text or "")
            city_id = None
            if city_name:
                city = await city_service.create(city_name)
                city_id = city.id
            await task_service.update(task_id, city_id=city_id)
        else:
            raise ValueError("Неизвестное поле")
    except ValueError as exc:
        await message.answer(str(exc))
        return

    await state.clear()
    updated = await task_service.get_admin_task_data(task_id)
    await message.answer(
        "Поле обновлено.\n\n" + get_admin_task_detail_text(updated),
        reply_markup=get_task_detail_keyboard(task_id, status=updated["status"], category_key=category_key, offset=offset),
    )


@router.callback_query(F.data.startswith("admin_task_activate:"))
async def task_activate(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id, category_key, offset = _parse_task_context(callback.data, "admin_task_activate")
    await task_service.set_status(task_id, TaskStatus.ACTIVE)
    await _render_task_detail(callback.message, task_id=task_id, category_key=category_key, offset=offset)
    await callback.answer("Задание активировано")


@router.callback_query(F.data.startswith("admin_task_hide:"))
async def task_hide(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id, category_key, offset = _parse_task_context(callback.data, "admin_task_hide")
    await task_service.set_status(task_id, TaskStatus.HIDDEN)
    await _render_task_detail(callback.message, task_id=task_id, category_key=category_key, offset=offset)
    await callback.answer("Задание скрыто")


@router.callback_query(F.data.startswith("admin_task_restart:"))
async def task_restart(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id, category_key, offset = _parse_task_context(callback.data, "admin_task_restart")
    await task_service.restart_task(task_id)
    await _render_task_detail(callback.message, task_id=task_id, category_key=category_key, offset=offset)
    await callback.answer("Задание перезапущено")


@router.callback_query(F.data.startswith("admin_task_delete_confirm:"))
async def task_delete_confirm(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id, category_key, offset = _parse_task_context(callback.data, "admin_task_delete_confirm")
    await callback.message.edit_text(
        f"Удалить задание #{task_id}?\nЭто действие нельзя отменить.",
        reply_markup=get_task_delete_confirm_keyboard(task_id, category_key=category_key, offset=offset),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_task_delete:"))
async def task_delete(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    task_id, category_key, offset = _parse_task_context(callback.data, "admin_task_delete")
    ok = await task_service.delete(task_id)
    if not ok:
        await callback.answer("Задание не найдено", show_alert=True)
        return
    await callback.answer("Задание удалено")
    await tasks_list_with_context(callback, category_key, 0 if offset < 0 else offset)


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
    users = await user_service.get_all_active_recipients()
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
        if await user_service.can_receive_bot_messages(item["user_id"]):
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
    await submission_service.reject_pending_submission(submission_id)
    try:
        if await user_service.can_receive_bot_messages(item["user_id"]):
            await callback.bot.send_message(item["user_id"], f"Задание #{item['task_id']} отклонено. Если нужна помощь, откройте раздел помощи в боте.")
    except Exception:
        pass
    item = await submission_service.get_admin_submission_data(submission_id)
    await callback.message.edit_text(
        get_admin_submission_detail_text(item),
        reply_markup=get_submission_detail_keyboard(submission_id, is_pending=False, has_screenshot=bool(item.get("screenshot_id"))),
    )
    await callback.answer("Задание отклонено")


async def _render_support_list(message: Message, *, offset: int = 0):
    unseen_count = await support_service.count_unseen()
    total = await support_service.count_all()
    requests = await support_service.get_page(limit=PAGE_SIZE, offset=offset)
    await message.edit_text(
        get_admin_support_requests_text(requests, unseen_count, offset=offset, total=total),
        reply_markup=get_support_list_keyboard(requests, offset=offset, total=total, limit=PAGE_SIZE),
    )


async def _render_support_request_detail(message: Message, *, request_id: int, back_callback: str):
    request = await support_service.get_by_id(request_id)
    if request is None or request.status.value == "deleted":
        await message.edit_text("Обращение не найдено или удалено.", reply_markup=build_back_keyboard("support"))
        return
    if not request.is_viewed:
        request = await support_service.mark_viewed(request_id) or request
    await message.edit_text(
        get_admin_support_request_detail_text(request),
        reply_markup=get_support_detail_keyboard(request.id, request.user_id, back_callback=back_callback),
    )


async def _render_support_history(message: Message, *, user_id: int, offset: int = 0):
    total = await support_service.count_user_history(user_id)
    requests = await support_service.get_user_history(user_id, limit=PAGE_SIZE, offset=offset)
    username = requests[0].username if requests else None
    await message.edit_text(
        get_admin_support_history_text(requests, username=username, user_id=user_id, offset=offset, total=total),
        reply_markup=get_support_history_keyboard(
            requests,
            user_id=user_id,
            offset=offset,
            total=total,
            limit=PAGE_SIZE,
            back_callback="support",
        ),
    )


@router.callback_query(F.data == "support")
async def admin_support(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    await _render_support_list(callback.message, offset=0)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_support:"))
async def admin_support_page(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    offset = int(callback.data.split(":", 1)[1])
    await _render_support_list(callback.message, offset=offset)
    await callback.answer()


@router.callback_query(F.data.startswith("admin_support_request:"))
async def admin_support_request_detail(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    _, request_id, offset = callback.data.split(":")
    await _render_support_request_detail(callback.message, request_id=int(request_id), back_callback=f"admin_support:{offset}")
    await callback.answer()


@router.callback_query(F.data.startswith("admin_support_history:"))
async def admin_support_history(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    _, user_id, offset = callback.data.split(":")
    await _render_support_history(callback.message, user_id=int(user_id), offset=int(offset))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_support_history_request:"))
async def admin_support_history_request_detail(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    _, request_id, user_id, offset = callback.data.split(":")
    await _render_support_request_detail(
        callback.message,
        request_id=int(request_id),
        back_callback=f"admin_support_history:{user_id}:{offset}",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_support_reply:"))
async def admin_support_reply_start(callback: CallbackQuery, state: FSMContext):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    request_id = int(callback.data.split(":", 1)[1])
    request = await support_service.get_by_id(request_id)
    if request is None or request.status.value == "deleted":
        await callback.answer("Обращение не найдено", show_alert=True)
        return
    await state.set_state(AdminSupportReplyState.waiting_text)
    await state.update_data(support_request_id=request_id, support_user_id=request.user_id)
    await callback.message.edit_text(
        "Введите ответ пользователю одним сообщением.",
        reply_markup=build_back_keyboard(f"admin_support_request:{request_id}:0"),
    )
    await callback.answer()


@router.message(AdminSupportReplyState.waiting_text)
async def admin_support_reply_finish(message: Message, state: FSMContext):
    if not await _ensure_admin(message.from_user.id):
        return
    if not message.text or not message.text.strip():
        await message.answer("Отправьте текстовый ответ.")
        return
    data = await state.get_data()
    request_id = int(data.get("support_request_id") or 0)
    user_id = data.get("support_user_id")
    request = await support_service.answer(request_id, admin_reply=message.text.strip(), answered_by=message.from_user.id)
    if request is None:
        await state.clear()
        await message.answer("Обращение не найдено.", reply_markup=build_back_keyboard("support"))
        return
    if user_id and await user_service.can_receive_bot_messages(int(user_id)):
        try:
            await message.bot.send_message(
                int(user_id),
                f"Ответ поддержки на Ваш запрос\n\n{message.text.strip()}",
            )
        except Exception:
            pass
    await state.clear()
    await message.answer(
        "Ответ отправлен пользователю.",
        reply_markup=build_back_keyboard(f"admin_support_request:{request_id}:0"),
    )


@router.callback_query(F.data.startswith("admin_support_delete:"))
async def admin_support_delete(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    request_id = int(callback.data.split(":", 1)[1])
    request = await support_service.delete(request_id)
    if request is None:
        await callback.answer("Обращение не найдено", show_alert=True)
        return
    await _render_support_list(callback.message, offset=0)
    await callback.answer("Обращение удалено")

@router.callback_query(F.data.startswith("admin_performer_delete:"))
async def performer_delete(callback: CallbackQuery):
    if not await _ensure_admin(callback.from_user.id):
        await callback.answer("Нет доступа", show_alert=True)
        return

    user_id = int(callback.data.split(":", 1)[1])

    if user_id == callback.from_user.id:
        await callback.answer("Нельзя удалить самого себя", show_alert=True)
        return

    user = await user_service.get_by_id(user_id)
    if user is None:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    await user_service.delete(user_id)

    await callback.message.edit_text(
        f"Пользователь ID {user_id} удалён.",
        reply_markup=build_back_keyboard("performers")
    )
    await callback.answer("Пользователь удалён")
