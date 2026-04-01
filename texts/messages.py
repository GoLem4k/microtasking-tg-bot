from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from config import (
    CHANNEL_URL,
    CHAT_URL,
    FAQ_URL,
    NEWS_CHANNEL_URL,
    REVIEWS_URL,
    SUPPORT_URL,
    WORKERS_CHAT_URL,
)

START_TEXT = """
* Добро пожаловать в Big Bucks
* Что это за бот? - Бот платит Вам за написание отзывов. Ежедневно мы собираем для Вас компании, которые поощряют своих клиентов за хорошие отзывы.

* Чтобы начать задание, нажмите кнопку “Приступить к заданию”
* Активные розыгрыши и акции [здесь будем давать ссылку]
* Чтобы не пропустить уведомления от бота о выполнении этапов НАСТОЯТЕЛЬНО РЕКОМЕНДУЕМ включить уведомления!
* Если у вас нету опыта по написанию отзывов на заказ, то рекомендуем ознакомиться с инструкциями  [ссылка на FAQ]
""".strip()

HELP_TEXT = """
🛟 В данном разделе указаны контакты поддержки для оперативного решения Ваших вопросов, а также ссылки на основные наши ресурсы.

⏰ Поддержка работает для Вас 24/7 без праздников и выходных.

🤝 Наша поддержка всегда поможет Вам с любыми проблемами при работе бота!
""".strip()

SUPPORT_PROMPT_TEXT = """
Напишите одним сообщением Ваш вопрос или проблему.

Сообщение будет отправлено в админку, после чего поддержка сможет с Вами связаться.
""".strip()

SUPPORT_REQUEST_SAVED_TEXT = """
Ваше сообщение отправлено в поддержку.

Ожидайте ответа администратора.
""".strip()

SUPPORT_EMPTY_TEXT = """
Пока обращений в поддержку нет.
""".strip()


def _format_amount(value: int | float | Decimal | None) -> str:
    if value is None:
        return "0"
    if isinstance(value, Decimal):
        value = value.normalize()
        text = format(value, "f")
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text or "0"
    if isinstance(value, float):
        text = f"{value:.2f}"
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text
    return str(value)


def get_profile_text(profile_data: dict) -> str:
    now_text = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    created_at = profile_data["created_at"]
    registration_days = max(0, (datetime.now().date() - created_at.date()).days)
    username = f"@{profile_data['username']}" if profile_data.get("username") else "не указан"
    status_raw = profile_data.get("status") or "user"
    status = status_raw.value if hasattr(status_raw, "value") else str(status_raw)
    balance = _format_amount(profile_data.get("balance", 0))
    task_earnings = _format_amount(profile_data.get("task_earnings", 0))
    referral_earnings = _format_amount(profile_data.get("total_referral_earnings", 0))

    warning_block = ""
    if profile_data.get("unfinished_count", 0) > 0:
        warning_block = "\n!! ВНИМАНИЕ! У ВАС ЕСТЬ НЕЗАКОНЧЕННОЕ ЗАДАНИЕ !!\n"

    return (
        "Личный кабинет\n\n"
        f"Дата и время: {now_text}\n"
        f"ID пользователя: {profile_data['user_id']}\n"
        f"Логин: {username}\n"
        f"Статус: {status}\n"
        f"Количество дней с момента регистрации: {registration_days}\n\n"
        f"Число выполненных заданий: {profile_data.get('approved_count', 0)}\n"
        f"Число заданий на проверке: {profile_data.get('pending_count', 0)}\n"
        f"{warning_block}"
        f"Текущий баланс: {balance}\n"
        f"Заработано за всё время с заданий: {task_earnings}\n"
        f"Заработано с рефералов: {referral_earnings}\n"
        f"Количество приглашенных рефералов 1 уровня: {profile_data.get('level1_count', 0)}\n"
        f"Количество приглашенных рефералов 2 уровня: {profile_data.get('level2_count', 0)}\n\n"
        "Место в ТОПе:\n"
        f"по заработку: {profile_data.get('rank_by_task_earnings', 1)}\n"
        f"по количеству рефералов: {profile_data.get('rank_by_referrals', 1)}\n"
        f"по заработку с рефералов: {profile_data.get('rank_by_referral_earnings', 1)}\n\n"
        "Ссылки:\n"
        f"Новостной канал: {NEWS_CHANNEL_URL or CHANNEL_URL}\n"
        f"Чат работников: {WORKERS_CHAT_URL or CHAT_URL}\n"
        f"Отзывы о нас: {REVIEWS_URL}\n"
        f"Поддержка: {SUPPORT_URL}\n"
    ).strip()


def get_referral_program_text(*, referral_link: str, level1_count: int, level2_count: int, level1_earnings: int, level2_earnings: int) -> str:
    total_earnings = level1_earnings + level2_earnings
    return f"""
Реферальная программа

Реферал 1 уровня — это человек, который впервые заходит в бота по вашей ссылке.
Когда человек зайдет в бота по вашей ссылке, он навсегда становится вашим рефералом 1 уровня.
Когда ваш реферал 1 уровня получает выплату за задание, вы получаете 20% от его заработка на ваш баланс.

Реферал 2 уровня — это человек, который впервые заходит в бота по ссылке вашего реферала 1 уровня.
Когда ваш реферал 2 уровня получает выплату за задание, вы получаете 5% от его заработка на ваш баланс.

Приглашайте новых пользователей и получайте пассивный доход от их заработка.

Ваши показатели:
• Рефералов 1 уровня: {level1_count}
• Рефералов 2 уровня: {level2_count}
• Заработано с 1 уровня: {level1_earnings}
• Заработано со 2 уровня: {level2_earnings}
• Всего заработано с рефералов: {total_earnings}

Ссылка для привлечения рефералов:
{referral_link}
""".strip()


def get_admin_main_text(stats: dict) -> str:
    return (
        "Админ меню\n\n"
        f"Пользователей в БД: {stats.get('users_total', 0)}\n"
        f"Всего заданий: {stats.get('tasks_total', 0)}\n"
        f"Активных заданий: {stats.get('tasks_active', 0)}\n"
        f"Заданий на проверке: {stats.get('pending_submissions', 0)}\n"
        f"Заявок на вывод в ожидании: {stats.get('pending_withdrawals', 0)}\n"
        f"Новых обращений в поддержку: {stats.get('new_support', 0)}"
    )


def get_admin_payments_overview_text(*, pending_count: int, approved_count: int, rejected_count: int, total_count: int) -> str:
    return (
        "Выплаты\n\n"
        f"Всего заявок: {total_count}\n"
        f"Ожидают обработки: {pending_count}\n"
        f"Одобрено: {approved_count}\n"
        f"Отклонено: {rejected_count}"
    )


def get_admin_payments_list_text(items, *, offset: int, total: int) -> str:
    lines = ["Заявки на вывод", "", f"Показано: {offset + 1}-{offset + len(items)} из {total}", ""]
    if not items:
        lines.append("Заявок пока нет.")
    else:
        for item in items:
            username = f"@{item.username}" if item.username else f"ID {item.user_id}"
            lines.append(f"#{item.id} | {username} | {item.amount}₽ | {item.method} | {item.status.value}")
    return "\n".join(lines).strip()


def get_admin_payments_detail_text(item) -> str:
    username = f"@{item.username}" if item.username else "без username"
    created = item.created_at.strftime("%d.%m.%Y %H:%M") if item.created_at else "-"
    processed = item.processed_at.strftime("%d.%m.%Y %H:%M") if item.processed_at else "-"
    return (
        f"Заявка на вывод #{item.id}\n\n"
        f"Статус: {item.status.value}\n"
        f"Дата создания: {created}\n"
        f"Дата обработки: {processed}\n"
        f"Пользователь: {username}\n"
        f"ID пользователя: {item.user_id}\n"
        f"Платежная система: {item.method}\n"
        f"Сумма: {item.amount} руб.\n"
        f"Реквизиты: {item.requisites or '-'}\n"
        f"Криптовалюта: {item.currency or '-'}\n"
        f"Комментарий админа: {item.admin_comment or '-'}"
    )


def get_admin_performers_list_text(items, *, offset: int, total: int) -> str:
    lines = ["Исполнители", "", f"Показано: {offset + 1}-{offset + len(items)} из {total}", ""]
    if not items:
        lines.append("Пользователей пока нет.")
    else:
        for item in items:
            username = f"@{item.username}" if item.username else f"ID {item.id}"
            lines.append(f"{username} | статус: {item.status.value} | баланс: {item.balance}")
    return "\n".join(lines).strip()


def get_admin_performer_detail_text(profile_data: dict) -> str:
    created_at = profile_data["created_at"].strftime("%d.%m.%Y %H:%M") if profile_data.get("created_at") else "-"
    username = f"@{profile_data['username']}" if profile_data.get("username") else "не указан"
    status_raw = profile_data.get("status") or "user"
    status = status_raw.value if hasattr(status_raw, "value") else str(status_raw)
    return (
        f"Исполнитель #{profile_data['user_id']}\n\n"
        f"Логин: {username}\n"
        f"Статус: {status}\n"
        f"Дата регистрации: {created_at}\n"
        f"Баланс: {_format_amount(profile_data.get('balance', 0))}\n"
        f"Выполнено заданий: {profile_data.get('approved_count', 0)}\n"
        f"На проверке: {profile_data.get('pending_count', 0)}\n"
        f"Незавершённых: {profile_data.get('unfinished_count', 0)}\n"
        f"Заработано с заданий: {_format_amount(profile_data.get('task_earnings', 0))}\n"
        f"Заработано с рефералов: {_format_amount(profile_data.get('total_referral_earnings', 0))}\n"
        f"Рефералов 1 уровня: {profile_data.get('level1_count', 0)}\n"
        f"Рефералов 2 уровня: {profile_data.get('level2_count', 0)}"
    )


def get_admin_tasks_list_text(items, *, offset: int, total: int) -> str:
    lines = ["Задания", "", f"Показано: {offset + 1}-{offset + len(items)} из {total}", ""]
    if not items:
        lines.append("Заданий пока нет.")
    else:
        for item in items:
            lines.append(
                f"#{item.id} | {item.title} | {int(item.reward)}₽ | {item.current_completions}/{item.max_completions} | {item.status.value}"
            )
    return "\n".join(lines).strip()


def get_admin_task_detail_text(data: dict) -> str:
    created_at = data.get("created_at")
    available_from = data.get("available_from")
    available_until = data.get("available_until")
    return (
        f"Задание #{data['id']}\n\n"
        f"Название: {data.get('title') or '-'}\n"
        f"Статус: {data.get('status')}\n"
        f"Цена: {_format_amount(data.get('reward', 0))} руб.\n"
        f"Выполнений: {data.get('current_completions', 0)}/{data.get('max_completions', 0)}\n"
        f"Город: {data.get('city_name') or '-'}\n"
        f"Точка/магазин: {data.get('shop_name') or '-'}\n"
        f"Адрес: {data.get('shop_address') or '-'}\n"
        f"Описание: {data.get('description') or '-'}\n"
        f"Примечание: {data.get('note') or '-'}\n"
        f"Доступно с: {available_from.strftime('%d.%m.%Y %H:%M') if available_from else '-'}\n"
        f"Доступно до: {available_until.strftime('%d.%m.%Y %H:%M') if available_until else '-'}\n"
        f"Создано: {created_at.strftime('%d.%m.%Y %H:%M') if created_at else '-'}"
    )


def get_admin_submissions_list_text(items: list[dict], *, offset: int, total: int) -> str:
    lines = ["Проверка заданий", "", f"Показано: {offset + 1}-{offset + len(items)} из {total}", ""]
    if not items:
        lines.append("Заданий на проверке нет.")
    else:
        for item in items:
            created = item["created_at"].strftime("%d.%m.%Y %H:%M") if item.get("created_at") else "-"
            username = f"@{item['username']}" if item['username'] != 'без username' else item['username']
            lines.append(f"#{item['id']} | {username} | {item['task_title']} | {created}")
    return "\n".join(lines).strip()


def get_admin_submission_detail_text(item: dict) -> str:
    created = item["created_at"].strftime("%d.%m.%Y %H:%M") if item.get("created_at") else "-"
    updated = item["updated_at"].strftime("%d.%m.%Y %H:%M") if item.get("updated_at") else "-"
    username = f"@{item['username']}" if item.get("username") and item.get("username") != "без username" else "без username"
    return (
        f"Проверка задания #{item['id']}\n\n"
        f"Статус: {item.get('status')}\n"
        f"Пользователь: {username}\n"
        f"ID пользователя: {item.get('user_id')}\n"
        f"ID задания: {item.get('task_id')}\n"
        f"Задание: {item.get('task_title') or '-'}\n"
        f"Награда: {item.get('reward', 0)} руб.\n"
        f"Скриншот: {'есть' if item.get('screenshot_id') else 'нет'}\n"
        f"Создано: {created}\n"
        f"Обновлено: {updated}"
    )


def get_admin_broadcast_confirm_text(text: str) -> str:
    return f"Рассылка\n\nТекст сообщения:\n{text}\n\nОтправить всем пользователям?"


def get_admin_support_requests_text(requests, unseen_count: int) -> str:
    if not requests:
        return SUPPORT_EMPTY_TEXT
    blocks = ["Поддержка", f"Новых обращений: {unseen_count}", ""]
    for request in requests:
        username = f"@{request.username}" if request.username else "без username"
        viewed = "новое" if not request.is_viewed else "просмотрено"
        created_at = request.created_at.strftime("%d.%m.%Y %H:%M")
        blocks.append(
            f"Заявка #{request.id}\n"
            f"Статус: {viewed}\n"
            f"Дата: {created_at}\n"
            f"Пользователь: {username} | ID: {request.user_id}\n"
            f"Текст: {request.message_text}"
        )
        blocks.append("")
    return "\n".join(blocks).strip()
