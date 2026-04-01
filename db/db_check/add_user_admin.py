from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

# Позволяет запускать файл напрямую:
# python db/db_check/add_user_admin.py
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.database import get_session  # noqa: E402
from db.models import City, ReferralSummary, User, UserStatus  # noqa: E402


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def ask_required(prompt: str) -> str:
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Поле обязательно для заполнения.")


def ask_optional(prompt: str) -> Optional[str]:
    value = input(prompt).strip()
    return value or None


def ask_optional_int(prompt: str) -> Optional[int]:
    while True:
        value = input(prompt).strip()
        if value == "":
            return None
        try:
            return int(value)
        except ValueError:
            print("Нужно ввести целое число или оставить поле пустым.")


def ask_status(prompt: str) -> UserStatus:
    while True:
        value = input(prompt).strip().lower()
        if value in ("", "user"):
            return UserStatus.USER
        if value == "admin":
            return UserStatus.ADMIN
        print("Статус должен быть 'user' или 'admin'.")


def ask_datetime(prompt: str) -> Optional[datetime]:
    while True:
        value = input(prompt).strip()
        if value == "":
            return None
        try:
            return datetime.strptime(value, DATETIME_FORMAT)
        except ValueError:
            print(f"Неверный формат даты. Используй {DATETIME_FORMAT}")


async def resolve_city(session, city_input: Optional[str]) -> Optional[int]:
    if not city_input:
        return None

    if city_input.isdigit():
        city = await session.get(City, int(city_input))
        if city is None:
            raise ValueError(f"Город с id={city_input} не найден.")
        return city.id

    normalized_name = city_input.strip().lower()
    stmt = select(City).where(City.name == normalized_name)
    result = await session.execute(stmt)
    city = result.scalars().first()

    if city:
        return city.id

    create_choice = input(
        f"Город '{normalized_name}' не найден. Создать его? [y/N]: "
    ).strip().lower()
    if create_choice not in {"y", "yes", "д", "да"}:
        raise ValueError("Создание пользователя отменено: город не существует.")

    city = City(name=normalized_name)
    session.add(city)
    await session.flush()
    return city.id


async def resolve_ref_parent_id(session, ref_input: Optional[str]) -> Optional[int]:
    if not ref_input:
        return None

    stmt = select(User).where(User.username == ref_input)
    result = await session.execute(stmt)
    ref_user = result.scalars().first()

    if ref_user is None:
        raise ValueError(f"Реферер с username='{ref_input}' не найден.")

    return ref_user.id


async def create_user_interactive() -> None:
    print("=== Создание пользователя ===")
    print("Пустое значение оставляет поле по умолчанию, где это разрешено.\n")

    manual_id = ask_optional_int("ID (Enter = автоинкремент): ")
    username = ask_required("Username: ")
    status = ask_status("Status [user/admin] (Enter = user): ")
    city_input = ask_optional("Город (id или name, Enter = NULL): ")
    ref_parent_username = ask_optional("Referral parent username (Enter = NULL): ")
    balance = ask_optional_int("Balance (Enter = 0): ")
    created_at = ask_datetime(
        f"Created at ({DATETIME_FORMAT}, Enter = now UTC): "
    )

    balance = 0 if balance is None else balance
    created_at = created_at or datetime.utcnow()

    async with get_session() as session:
        existing_stmt = select(User).where(User.username == username)
        existing_result = await session.execute(existing_stmt)
        existing_user = existing_result.scalars().first()
        if existing_user is not None:
            raise ValueError(f"Пользователь '{username}' уже существует.")

        city_id = await resolve_city(session, city_input)
        ref_parent_id = await resolve_ref_parent_id(session, ref_parent_username)

        user = User(
            username=username,
            status=status,
            city_id=city_id,
            ref_parent_id=ref_parent_id,
            balance=balance,
            created_at=created_at,
        )

        if manual_id is not None:
            user.id = manual_id

        session.add(user)
        await session.flush()

        referral_summary = ReferralSummary(user_id=user.id)
        session.add(referral_summary)
        await session.flush()
        await session.refresh(user)

        print("\nПользователь успешно создан:")
        print(f"  id        : {user.id}")
        print(f"  username  : {user.username}")
        print(f"  status    : {user.status.value}")
        print(f"  city_id   : {user.city_id}")
        print(f"  ref_parent: {user.ref_parent_id}")
        print(f"  balance   : {user.balance}")
        print(f"  created_at: {user.created_at}")


async def main() -> None:
    try:
        await create_user_interactive()
    except IntegrityError as exc:
        print("\nОшибка целостности БД:", exc)
    except ValueError as exc:
        print(f"\nОшибка: {exc}")
    except KeyboardInterrupt:
        print("\nОперация прервана пользователем.")


if __name__ == "__main__":
    asyncio.run(main())
