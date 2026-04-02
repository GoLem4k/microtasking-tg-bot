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

#🤝✍️📍🆔🎁⚠️⚜️❗️🫂💰🧾🔝✅🔗⏳🛡🛠📑💼🗣💫📌💸💵💎⚙️🔧💳📖⛔️◀️♻️📱👫🖥📲⏰📝🔉☝️❌🗺🍀🏘🔙

START_TEXT = """
🤝 Добро пожаловать в <b>Big Bucks</b>
✍️ Что это за бот? — Бот платит Вам за написание отзывов. Ежедневно мы собираем для Вас компании, которые поощряют своих клиентов за хорошие отзывы.

✍️ Чтобы начать задание, нажмите кнопку “<b>Приступить к заданию</b>”
🎁 Активные розыгрыши и акции <a href="ССЫЛКА">здесь</a>
⚠️ Чтобы не пропустить уведомления от бота о выполнении этапов <u><b>НАСТОЯТЕЛЬНО РЕКОМЕНДУЕМ</b></u> включить уведомления!
🧾 Если у вас нет опыта по написанию отзывов на заказ, рекомендуем ознакомиться с инструкциями <a href="https://en.wikipedia.org/wiki/Telegram_(software)">FAQ</a>
""".strip()

HELP_TEXT = """
📲 В данном разделе указаны контакты поддержки для оперативного решения Ваших вопросов, а также ссылки на основные наши ресурсы.

⏰ Поддержка работает для Вас 24/7 без праздников и выходных.

🤝 Наша поддержка всегда поможет Вам с любыми проблемами при работе бота!
""".strip()

SUPPORT_PROMPT_TEXT = """
✍️ Напишите одним сообщением Ваш вопрос или проблему.

❗ Сообщение будет отправлено в поддержку, после чего администратор сможет связаться с Вами.
""".strip()

SUPPORT_REQUEST_SAVED_TEXT = """
✅ Ваше сообщение отправлено в поддержку.

Ожидайте ответа администратора.
""".strip()

SUPPORT_EMPTY_TEXT = """
Пока обращений в поддержку нет.
""".strip()

RULES_TEXT = """
📌 Перед началом задания ознакомьтесь с правилами:

❗️ Отзыв должен быть написан грамотно, без орфографических и пунктуационных ошибок.
❗️ Возраст аккаунта на площадке должен быть больше месяца.
❗️ Имя аккаунта должно выглядеть естественно, как имя реального человека.
❗️ Нельзя использовать несколько Telegram-аккаунтов для работы в боте.

Если Вы согласны с правилами, переходите дальше.
""".strip()

CITY_PROMPT_TEXT = """
📍 Для подбора заданий укажите Ваш город.

Отправьте его одним сообщением. Если Вы живёте рядом с небольшим населённым пунктом, можно указать ближайший крупный город.

Это нужно, чтобы показывать Вам задания с максимальным шансом прохождения модерации.
""".strip()

MAIN_TASKS_PLATFORM_TEXT = """
🎯 Сейчас для Вас доступны следующие платформы.

Платформа может временно отсутствовать, если задания на ней уже закончились.

Важно соблюдать интервалы публикации отзывов с одного аккаунта:
• Google Maps — 1 отзыв в 2 дня
• Яндекс.Карты — 1 отзыв в 4 дня
• 2ГИС — 1 отзыв в 2 дня
• Авито — 1 отзыв в 3 дня
• Яндекс — 1 отзыв в 4 дня
• ВК — 1 отзыв в 2 дня
• ZOON — 1 отзыв в 2 дня
• Irecommend — 1 отзыв в 3 дня
• Otzovik.com — 1 отзыв в 3 дня

Если нарушать эти интервалы, отзыв может не пройти модерацию, а аккаунт может быть заблокирован.

Выберите платформу из списка ниже:
""".strip()

MAIN_TASKS_EMPTY_TEXT = """
😔 Сейчас в Вашей локации нет доступных заданий.

Если город не совпадает с заданиями по гео, мы показываем только те задания, где география не важна.
Попробуйте зайти позже или загляните в раздел дополнительных заданий.
""".strip()

TASK_IN_PROGRESS_SCREENSHOT_TEXT = """
📸 Отправьте скриншот Вашего отзыва.

На отправку есть 1 час. После получения скриншота задание перейдёт в статус «на проверке».
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
        f"🗓 Дата и время: {now_text}\n"
        f"🆔 ID пользователя: {profile_data['user_id']}\n"
        f"⚜️ Логин: {username}\n"
        f"💫 Статус: {status}\n"
        f"🫂 Количество дней с момента регистрации: {registration_days}\n\n"
        f"✅ Число выполненных заданий: {profile_data.get('approved_count', 0)}\n"
        f"⏳ Число заданий на проверке: {profile_data.get('pending_count', 0)}\n"
        f"{warning_block}"
        f"💰 Текущий баланс: {balance}\n"
        f"🧾 Заработано за всё время с заданий: {task_earnings}\n"
        f"🤝 Заработано с рефералов: {referral_earnings}\n"
        f"🔗 Количество приглашенных рефералов 1 уровня: {profile_data.get('level1_count', 0)}\n"
        f"🔗 Количество приглашенных рефералов 2 уровня: {profile_data.get('level2_count', 0)}\n\n"
        "🔝 Место в ТОПе:\n"
        f"├по заработку: {profile_data.get('rank_by_task_earnings', 1)}\n"
        f"├по количеству рефералов: {profile_data.get('rank_by_referrals', 1)}\n"
        f"└по заработку с рефералов: {profile_data.get('rank_by_referral_earnings', 1)}\n\n"
        "Ссылки:\n"
        f"🗣 Новостной канал: {NEWS_CHANNEL_URL or CHANNEL_URL}\n"
        f"💼 Чат работников: {WORKERS_CHAT_URL or CHAT_URL}\n"
        f"📑 Отзывы о нас: {REVIEWS_URL}\n"
        f"🛠 Поддержка: {SUPPORT_URL}\n"
    ).strip()


def get_referral_program_text(*, referral_link: str, level1_count: int, level2_count: int, level1_earnings: int, level2_earnings: int) -> str:
    total_earnings = level1_earnings + level2_earnings
    return f"""
<u><b>Реферальная программа</b></u>
❗️ Реферал 1 уровня — это человек, который впервые заходит в бота по вашей ссылке.
Когда человек зайдет в бота по вашей ссылке, он навсегда становится вашим рефералом 1 уровня.
Когда ваш реферал 1 уровня получает выплату за задание, вы получаете 20% от его заработка на ваш баланс.

❗️ Реферал 2 уровня — это человек, который впервые заходит в бота по ссылке вашего реферала 1 уровня.
Когда ваш реферал 2 уровня получает выплату за задание, вы получаете 5% от его заработка на ваш баланс.

✅ Приглашайте новых пользователей и получайте пассивный доход от их заработка.

🧾 Ваши показатели:
• Рефералов 1 уровня: {level1_count}
• Рефералов 2 уровня: {level2_count}
• Заработано с 1 уровня: {level1_earnings}
• Заработано со 2 уровня: {level2_earnings}
• Всего заработано с рефералов: {total_earnings}

👁‍🗨 Ссылка для привлечения рефералов:
{referral_link}
""".strip()


def get_admin_main_text(stats: dict) -> str:
    return (
        "⚙️ Админ-панель\n\n"
        f"Пользователей в БД: {stats.get('users_total', 0)}\n"
        f"Всего заданий: {stats.get('tasks_total', 0)}\n"
        f"Активных заданий: {stats.get('tasks_active', 0)}\n"
        f"Заданий на проверке: {stats.get('pending_submissions', 0)}\n"
        f"Заявок на вывод в ожидании: {stats.get('pending_withdrawals', 0)}\n"
        f"Новых обращений в поддержку: {stats.get('new_support', 0)}"
    )


def get_admin_payments_overview_text(*, pending_count: int, approved_count: int, rejected_count: int, total_count: int) -> str:
    return (
        "💳 Выплаты\n\n"
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
    lines = ["👥 Исполнители", "", f"Показано: {offset + 1}-{offset + len(items)} из {total}", ""]
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
        f"👤 Исполнитель #{profile_data['user_id']}\n\n"
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


def get_admin_tasks_list_text(items, *, offset: int, total: int, category_label: str = "Все") -> str:
    lines = ["📋 Задания", "", f"Фильтр: {category_label}", f"Показано: {offset + 1}-{offset + len(items)} из {total}", ""]
    if not items:
        lines.append("Заданий пока нет.")
    else:
        for item in items:
            category = item.category.value if hasattr(item.category, "value") else str(item.category)
            category = {"main": "обычное", "extra": "доп."}.get(category, category)
            status = {"active": "active", "hidden": "hidden", "completed": "completed"}.get(item.status.value, item.status.value)
            lines.append(
                f"#{item.id} | [{category}] {item.title} | {int(item.reward)}₽ | {item.current_completions}/{item.max_completions} | {status}"
            )
    return "\n".join(lines).strip()


def get_admin_task_detail_text(data: dict) -> str:
    created_at = data.get("created_at")
    available_from = data.get("available_from")
    available_until = data.get("available_until")
    category_map = {"main": "Обычное", "extra": "Дополнительное"}
    status_map = {"active": "Активно", "hidden": "Скрыто", "completed": "Завершено"}
    category = category_map.get(data.get("category") or "main", data.get("category") or "main")
    status = status_map.get(data.get("status") or "-", data.get("status") or "-")
    return (
        f"📌 Задание #{data['id']}\n\n"
        f"Категория: {category}\n"
        f"Площадка / кнопка: {data.get('title') or '-'}\n"
        f"Название / объект: {data.get('description') or '-'}\n"
        f"Статус: {status}\n"
        f"Цена: {_format_amount(data.get('reward', 0))} руб.\n"
        f"Выполнений: {data.get('current_completions', 0)}/{data.get('max_completions', 0)}\n"
        f"Город: {data.get('city_name') or '-'}\n"
        f"Точка/магазин: {data.get('shop_name') or '-'}\n"
        f"Адрес: {data.get('shop_address') or '-'}\n"
        f"Инструкция / примечание: {data.get('note') or '-'}\n"
        f"Доступно с: {available_from.strftime('%d.%m.%Y %H:%M') if available_from else '-'}\n"
        f"Доступно до: {available_until.strftime('%d.%m.%Y %H:%M') if available_until else '-'}\n"
        f"Создано: {created_at.strftime('%d.%m.%Y %H:%M') if created_at else '-'}"
    )


def get_admin_submissions_list_text(items: list[dict], *, offset: int, total: int) -> str:
    lines = ["🛠 Проверка заданий", "", f"Показано: {offset + 1}-{offset + len(items)} из {total}", ""]
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
    performer_login = item.get("performer_login") or "-"
    status_map = {
        "in_progress": "незавершённое",
        "pending": "на проверке",
        "approved": "подтверждено",
        "rejected": "отклонено",
    }
    return (
        f"🧾 Проверка задания #{item['id']}\n\n"
        f"Статус: {status_map.get(item.get('status'), item.get('status'))}\n"
        f"Пользователь: {username}\n"
        f"ID пользователя: {item.get('user_id')}\n"
        f"ID задания: {item.get('task_id')}\n"
        f"Задание: {item.get('task_title') or '-'}\n"
        f"Логин исполнителя: {performer_login}\n"
        f"Награда: {item.get('reward', 0)} руб.\n"
        f"Скриншот: {'есть' if item.get('screenshot_id') else 'нет'}\n"
        f"Создано: {created}\n"
        f"Обновлено: {updated}"
    )


def get_admin_broadcast_confirm_text(text: str) -> str:
    return f"📣 Рассылка\n\nТекст сообщения:\n{text}\n\nОтправить всем пользователям?"


def get_admin_support_requests_text(requests, unseen_count: int, *, offset: int = 0, total: int | None = None) -> str:
    total_line = f"\nПоказано: {offset + 1}-{offset + len(requests)} из {total}" if total is not None and requests else ""
    if not requests:
        return f"🆘 Поддержка\n\nНовых обращений: {unseen_count}\n\nОбращений пока нет."
    return f"🆘 Поддержка\n\nНовых обращений: {unseen_count}{total_line}\n\nВыберите обращение из списка ниже."


def get_admin_support_request_detail_text(request) -> str:
    username = f"@{request.username}" if request.username else "без username"
    reply_block = f"\n\nОтвет: {request.admin_reply}" if request.admin_reply else ""
    return (
        f"ID: {request.user_id or '-'}\n"
        f"Username: {username}\n"
        f"Вопрос: {request.message_text}{reply_block}"
    )


def get_admin_support_history_text(requests, *, username: str | None, user_id: int, offset: int, total: int) -> str:
    header_username = f"@{username}" if username else "без username"
    lines = [
        "🗂 История запросов",
        "",
        f"Пользователь: {header_username}",
        f"ID: {user_id}",
        f"Показано: {offset + 1}-{offset + len(requests)} из {total}" if requests else f"Показано: 0 из {total}",
        "",
    ]
    if not requests:
        lines.append("Обращений не найдено.")
    else:
        for request in requests:
            created_at = request.created_at.strftime("%d.%m.%Y %H:%M") if request.created_at else "-"
            lines.append(f"#{request.id} | {request.status.value} | {created_at}")
    return "\n".join(lines).strip()






def get_task_variants_list_text(*, platform_name: str, reward_text: str, count: int) -> str:
    return (
        f"📚 На платформе {platform_name} сейчас доступно несколько заданий по {reward_text} ₽.\n\n"
        f"Найдено вариантов: {count}. Выберите нужное задание из списка ниже:"
    )


def get_task_card_text(*, platform_name: str, city_name: str, task_name: str, reward_text: str) -> str:
    return (
        f"Вы выбрали задание: {platform_name}\n"
        f"Город: {city_name}\n"
        f"Название: {task_name}\n"
        f"Цена: {reward_text} руб.\n\n"
        "Выполнение задания занимает около 5–15 минут!"
    )


def get_task_instruction_text(*, platform_name: str, instruction_url: str | None) -> str:
    instruction_line = instruction_url or "Инструкция пока не добавлена. Обратитесь в поддержку."
    return (
        "После ознакомления с инструкцией приступайте к работе.\n\n"
        f"Открыть инструкцию: {instruction_line}\n"
        f"Если инструкция не открывается, обратитесь в поддержку: {SUPPORT_URL}\n\n"
        "Чтобы не пропустить уведомления от бота о выполнении этапов, настоятельно рекомендуем включить уведомления.\n\n"
        f"Напишите Ваш логин, который используется на площадке {platform_name} для публикации отзыва:"
    )


def get_task_submission_saved_text(*, reward_text: str, balance_text: str) -> str:
    return f"""
🥳 Данные получены.

👌 Мы проверим Ваш отзыв через 4 дня. Если на 3-и сутки, не считая день написания, отзыв прошёл, то мы пополним Ваш баланс в боте на {reward_text} ₽ за оставленный отзыв.

Например: если Вы написали отзыв 1 числа и он прошёл модерацию и виден всем, то мы переведём оплату 4-го числа до 23:59 по МСК.

Проверить, прошёл отзыв или нет, Вы можете сами через вкладку инкогнито или выйдя из своего аккаунта и найдя отзыв. Если отзыв не прошёл с первого раза, значит, он уже не пройдёт.

☝ Напоминаем: мы платим только за опубликованные отзывы, которые прошли модерацию и видны всем.

⁉ Почему нужно ждать 4 суток?
Отзыв может быть опубликован и виден всем уже через 1–2 дня, но на 3-и сутки отзыв могут скрыть. Нам нужно убедиться, что отзыв прошёл полную модерацию и виден всем на 4-е сутки.

Ваш текущий баланс в боте: {balance_text} ₽.

👌 Напоминаем: если на Вашем балансе в боте более 200 рублей, Вы можете перевести их на мобильный телефон, а если более 500 рублей — вывести на банковскую карту.

🙏 Благодарим за работу!
""".strip()


def get_unfinished_task_warning_text(*, platform_name: str, started_at, instruction_url: str | None) -> str:
    started_text = started_at.strftime("%d.%m.%Y %H:%M") if started_at else "-"
    instruction_line = instruction_url or "Инструкция пока не добавлена"
    return (
        "У Вас есть незаконченное задание:\n\n"
        f"Платформа: {platform_name}\n"
        f"Дата и время начала: {started_text}\n"
        f"Ссылка на инструкцию: {instruction_line}"
    )
