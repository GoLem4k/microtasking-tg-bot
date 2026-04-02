from __future__ import annotations

from decimal import Decimal

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from db.models import Task, TaskCategory
from db.services.cities_service import CityService
from db.services.task_submissions_service import TaskSubmissionService
from db.services.tasks_service import TaskService
from db.services.users_service import UserService
from filters.is_admin import is_admin
from keyboards.admin.task_check import get_submission_detail_keyboard
from keyboards.main_menu import get_main_keyboard
from keyboards.task_flow import (
    get_city_request_keyboard,
    get_no_tasks_keyboard,
    get_task_detail_keyboard,
    get_task_platforms_keyboard,
    get_task_rules_keyboard,
    get_task_variants_keyboard,
    get_unfinished_task_keyboard,
)
from states.task_flow import TaskFlowState
from texts.messages import (
    CITY_PROMPT_TEXT,
    MAIN_TASKS_EMPTY_TEXT,
    MAIN_TASKS_PLATFORM_TEXT,
    RULES_TEXT,
    TASK_IN_PROGRESS_SCREENSHOT_TEXT,
    get_admin_submission_detail_text,
    get_task_card_text,
    get_task_instruction_text,
    get_task_submission_saved_text,
    get_task_variants_list_text,
    get_unfinished_task_warning_text,
)
from utils.admin_alerts import send_admin_alert

router = Router()

task_service = TaskService()
submission_service = TaskSubmissionService()
user_service = UserService()
city_service = CityService()


async def _get_main_keyboard_for_user(user_id: int):
    admin_flag = await is_admin(user_id)
    return get_main_keyboard(user_id, is_admin_flag=admin_flag)


async def send_text(target: CallbackQuery | Message, text: str, *, reply_markup=None) -> None:
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
        await target.answer()
    else:
        await target.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)


async def cleanup_expired_submissions(user_id: int) -> int:
    return await submission_service.cleanup_expired_in_progress(user_id=user_id, hours=24)


async def show_unfinished_warning_if_needed(target: CallbackQuery | Message) -> bool:
    user_id = target.from_user.id
    submission = await submission_service.get_in_progress_for_user(user_id)
    if submission is None:
        return False

    await send_text(
        target,
        get_unfinished_task_warning_text(
            platform_name=submission.get("task_title") or "-",
            started_at=submission.get("created_at"),
            instruction_url=submission.get("instruction_url"),
        ),
        reply_markup=get_unfinished_task_keyboard(),
    )
    return True


async def begin_city_request(target: CallbackQuery | Message, state: FSMContext, *, category: TaskCategory) -> None:
    await state.set_state(TaskFlowState.waiting_city)
    await state.update_data(category=category.value)
    await send_text(target, CITY_PROMPT_TEXT, reply_markup=get_city_request_keyboard())



def parse_task_id(callback_data: str) -> int:
    return int(callback_data.split(":", 1)[1])



def format_reward(value: int | float | Decimal | None) -> str:
    if value is None:
        return "0"
    if isinstance(value, Decimal):
        value = value.normalize()
        text = format(value, "f")
        return text.rstrip("0").rstrip(".") if "." in text else text
    if isinstance(value, float):
        text = f"{value:.2f}"
        return text.rstrip("0").rstrip(".") if "." in text else text
    return str(int(value))



def _task_group_key(task: Task) -> tuple[str, str]:
    return ((task.title or "").strip().lower(), format_reward(task.reward))



def _group_tasks_by_platform_and_reward(tasks: list[Task]) -> list[list[Task]]:
    grouped: dict[tuple[str, str], list[Task]] = {}
    for task in tasks:
        grouped.setdefault(_task_group_key(task), []).append(task)
    return list(grouped.values())



def _build_task_variant_button_text(task: Task) -> str:
    description = (task.description or "").strip()
    if not description:
        return f"Задание #{task.id}"
    short_description = description if len(description) <= 48 else description[:45].rstrip() + "..."
    return short_description


async def _get_available_tasks_for_user(*, user_id: int, category: TaskCategory) -> list[Task]:
    user = await user_service.get_by_id(user_id)
    city_id = user.city_id if user else None
    return await task_service.get_available_for_user(city_id=city_id, category=category)


async def show_tasks_for_category(target: CallbackQuery | Message, *, user_id: int, category: TaskCategory) -> None:
    tasks = await _get_available_tasks_for_user(user_id=user_id, category=category)

    if not tasks:
        empty_text = MAIN_TASKS_EMPTY_TEXT if category == TaskCategory.MAIN else "🧩 Сейчас дополнительные задания недоступны. Загляните позже."
        await send_text(
            target,
            empty_text,
            reply_markup=get_no_tasks_keyboard(include_extra_button=(category == TaskCategory.MAIN)),
        )
        return

    grouped_tasks = _group_tasks_by_platform_and_reward(tasks)
    buttons: list[tuple[str, str]] = []
    for group in grouped_tasks:
        representative = group[0]
        reward_text = format_reward(representative.reward)
        callback_data = f"task_group:{representative.id}" if len(group) > 1 else f"task_detail:{representative.id}"
        buttons.append((f"{representative.title} | {reward_text} ₽", callback_data))

    if category == TaskCategory.MAIN:
        await send_text(
            target,
            MAIN_TASKS_PLATFORM_TEXT,
            reply_markup=get_task_platforms_keyboard(buttons, include_extra_button=True),
        )
        return

    await send_text(
        target,
        "🧩 Сейчас доступны дополнительные задания. Выберите подходящую площадку ниже.",
        reply_markup=get_task_platforms_keyboard(buttons, include_extra_button=False),
    )


async def resume_in_progress_submission(callback: CallbackQuery, state: FSMContext) -> None:
    submission = await submission_service.get_in_progress_for_user(callback.from_user.id)
    if submission is None:
        await callback.answer("Незаконченных заданий нет", show_alert=True)
        return

    task_data = await task_service.get_public_task_data(submission["task_id"])
    if task_data is None:
        await callback.answer("Задание не найдено", show_alert=True)
        return

    if submission.get("performer_login"):
        await state.set_state(TaskFlowState.waiting_screenshot)
        await state.update_data(submission_id=submission["id"], task_id=submission["task_id"])
        await callback.message.edit_text(
            TASK_IN_PROGRESS_SCREENSHOT_TEXT,
            reply_markup=get_city_request_keyboard(),
            disable_web_page_preview=True,
        )
        await callback.answer()
        return

    await state.set_state(TaskFlowState.waiting_platform_login)
    await state.update_data(submission_id=submission["id"], task_id=submission["task_id"])
    await callback.message.edit_text(
        get_task_instruction_text(
            platform_name=task_data.get("title") or "площадке",
            instruction_url=task_data.get("note"),
        ),
        reply_markup=get_city_request_keyboard(),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.message(Command("task"))
async def start_task_command(message: Message, state: FSMContext):
    await state.clear()
    await cleanup_expired_submissions(message.from_user.id)

    if await show_unfinished_warning_if_needed(message):
        return

    await message.answer(RULES_TEXT, reply_markup=get_task_rules_keyboard(), disable_web_page_preview=True)


@router.callback_query(F.data == "start_task")
async def start_task(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await cleanup_expired_submissions(callback.from_user.id)

    if await show_unfinished_warning_if_needed(callback):
        return

    await callback.message.edit_text(RULES_TEXT, reply_markup=get_task_rules_keyboard(), disable_web_page_preview=True)
    await callback.answer()


@router.callback_query(F.data == "task_unfinished_continue")
async def task_unfinished_continue(callback: CallbackQuery, state: FSMContext):
    await resume_in_progress_submission(callback, state)


@router.callback_query(F.data == "task_unfinished_cancel")
async def task_unfinished_cancel(callback: CallbackQuery, state: FSMContext):
    await submission_service.delete_in_progress_for_user(callback.from_user.id)
    await state.clear()

    keyboard = await _get_main_keyboard_for_user(callback.from_user.id)
    await callback.message.edit_text("🗑 Незавершённое задание аннулировано. Вы вернулись в главное меню.", reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("task_rules_accept:"))
async def task_rules_accept(callback: CallbackQuery, state: FSMContext):
    category_raw = callback.data.split(":", 1)[1]
    category = TaskCategory.EXTRA if category_raw == TaskCategory.EXTRA.value else TaskCategory.MAIN
    await begin_city_request(callback, state, category=category)


@router.message(TaskFlowState.waiting_city)
async def task_city_received(message: Message, state: FSMContext):
    city_name = (message.text or "").strip()
    if not city_name:
        await message.answer("Напишите город текстом одним сообщением.")
        return

    state_data = await state.get_data()
    category_raw = state_data.get("category", TaskCategory.MAIN.value)
    category = TaskCategory.EXTRA if category_raw == TaskCategory.EXTRA.value else TaskCategory.MAIN

    city = await city_service.create(city_name)
    await user_service.update(message.from_user.id, city_id=city.id)
    await state.clear()

    await show_tasks_for_category(message, user_id=message.from_user.id, category=category)


@router.callback_query(F.data.startswith("task_show_list:"))
async def task_show_list(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    category_raw = callback.data.split(":", 1)[1]
    category = TaskCategory.EXTRA if category_raw == TaskCategory.EXTRA.value else TaskCategory.MAIN
    await show_tasks_for_category(callback, user_id=callback.from_user.id, category=category)


@router.callback_query(F.data.startswith("task_group:"))
async def task_group(callback: CallbackQuery):
    task_id = parse_task_id(callback.data)
    representative = await task_service.get_by_id(task_id)
    if representative is None:
        await callback.answer("Группа заданий не найдена", show_alert=True)
        return

    category = representative.category if representative.category else TaskCategory.MAIN
    tasks = await _get_available_tasks_for_user(user_id=callback.from_user.id, category=category)
    representative_key = _task_group_key(representative)
    matching_tasks = [task for task in tasks if _task_group_key(task) == representative_key]

    if not matching_tasks:
        await callback.answer("Доступных заданий не найдено", show_alert=True)
        return

    if len(matching_tasks) == 1:
        task = matching_tasks[0]
        task_data = await task_service.get_public_task_data(task.id)
        if task_data is None:
            await callback.answer("Задание не найдено", show_alert=True)
            return
        await callback.message.edit_text(
            get_task_card_text(
                platform_name=task_data.get("title") or "-",
                city_name=task_data.get("city_name") or "любой город",
                task_name=task_data.get("description") or task_data.get("title") or "-",
                reward_text=format_reward(task_data.get("reward")),
            ),
            reply_markup=get_task_detail_keyboard(task.id, category=task_data.get("category") or TaskCategory.MAIN.value),
            disable_web_page_preview=True,
        )
        await callback.answer()
        return

    buttons = [(_build_task_variant_button_text(task), f"task_detail:{task.id}") for task in matching_tasks]
    await callback.message.edit_text(
        get_task_variants_list_text(
            platform_name=representative.title or "Площадка",
            reward_text=format_reward(representative.reward),
            count=len(matching_tasks),
        ),
        reply_markup=get_task_variants_keyboard(buttons, category=category.value),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task_detail:"))
async def task_detail(callback: CallbackQuery):
    task_id = parse_task_id(callback.data)
    task_data = await task_service.get_public_task_data(task_id)
    if task_data is None:
        await callback.answer("Задание не найдено", show_alert=True)
        return

    await callback.message.edit_text(
        get_task_card_text(
            platform_name=task_data.get("title") or "-",
            city_name=task_data.get("city_name") or "любой город",
            task_name=task_data.get("description") or task_data.get("title") or "-",
            reward_text=format_reward(task_data.get("reward")),
        ),
        reply_markup=get_task_detail_keyboard(task_id, category=task_data.get("category") or TaskCategory.MAIN.value),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task_start_selected:"))
async def task_start_selected(callback: CallbackQuery, state: FSMContext):
    await cleanup_expired_submissions(callback.from_user.id)
    if await show_unfinished_warning_if_needed(callback):
        return

    task_id = parse_task_id(callback.data)
    task_data = await task_service.get_public_task_data(task_id)
    if task_data is None:
        await callback.answer("Задание не найдено", show_alert=True)
        return

    submission = await submission_service.create_for_user(user_id=callback.from_user.id, task_id=task_id)
    if submission is None:
        await callback.answer("Не удалось взять задание. Возможно, лимит уже исчерпан.", show_alert=True)
        return

    await state.set_state(TaskFlowState.waiting_platform_login)
    await state.update_data(submission_id=submission.id, task_id=task_id)

    await callback.message.edit_text(
        get_task_instruction_text(
            platform_name=task_data.get("title") or "площадке",
            instruction_url=task_data.get("note"),
        ),
        reply_markup=get_city_request_keyboard(),
        disable_web_page_preview=True,
    )
    await callback.answer()


@router.message(TaskFlowState.waiting_platform_login)
async def task_platform_login_received(message: Message, state: FSMContext):
    performer_login = (message.text or "").strip()
    if not performer_login:
        await message.answer("Отправьте логин одним сообщением.")
        return

    state_data = await state.get_data()
    submission_id = state_data.get("submission_id")
    task_id = state_data.get("task_id")
    if not submission_id or not task_id:
        await state.clear()
        await message.answer("Сессия задания сброшена. Начните заново через кнопку «Приступить к заданию».")
        return

    await submission_service.set_performer_login(submission_id, performer_login)
    await state.set_state(TaskFlowState.waiting_screenshot)
    await state.update_data(submission_id=submission_id, task_id=task_id)
    await message.answer(TASK_IN_PROGRESS_SCREENSHOT_TEXT, reply_markup=get_city_request_keyboard(), disable_web_page_preview=True)


@router.message(TaskFlowState.waiting_screenshot, F.photo)
async def task_screenshot_received(message: Message, state: FSMContext):
    state_data = await state.get_data()
    submission_id = state_data.get("submission_id")
    task_id = state_data.get("task_id")
    if not submission_id or not task_id:
        await state.clear()
        await message.answer("Сессия задания сброшена. Начните заново через кнопку «Приступить к заданию».")
        return

    photo = message.photo[-1]
    await submission_service.submit_for_review(submission_id, screenshot_id=photo.file_id)
    task_data = await task_service.get_public_task_data(task_id)
    admin_submission = await submission_service.get_admin_submission_data(submission_id)
    if admin_submission is not None:
        await send_admin_alert(
            message.bot,
            get_admin_submission_detail_text(admin_submission),
            reply_markup=get_submission_detail_keyboard(
                submission_id,
                is_pending=admin_submission.get("status") == "pending",
                has_screenshot=bool(admin_submission.get("screenshot_id")),
            ),
        )
    user = await user_service.get_by_id(message.from_user.id)
    await state.clear()

    keyboard = await _get_main_keyboard_for_user(message.from_user.id)
    await message.answer(
        get_task_submission_saved_text(
            reward_text=format_reward(task_data.get("reward") if task_data else 0),
            balance_text=format_reward(user.balance if user else 0),
        ),
        reply_markup=keyboard,
        disable_web_page_preview=True,
    )


@router.message(TaskFlowState.waiting_screenshot)
async def task_screenshot_invalid(message: Message):
    await message.answer("Пожалуйста, отправьте именно скриншот в виде фото.")
