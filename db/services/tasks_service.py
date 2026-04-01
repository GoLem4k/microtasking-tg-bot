from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Sequence

from sqlalchemy import and_, func, select

from db.database import get_session
from db.models import City, Shop, Task, TaskStatus


class TaskService:
    async def get_by_id(self, task_id: int) -> Task | None:
        async with get_session() as session:
            return await session.get(Task, task_id)

    async def get_all(self) -> Sequence[Task]:
        async with get_session() as session:
            stmt = select(Task).order_by(Task.id)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def count_all(self) -> int:
        async with get_session() as session:
            stmt = select(func.count()).select_from(Task)
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)

    async def count_active(self) -> int:
        async with get_session() as session:
            stmt = select(func.count()).select_from(Task).where(Task.status == TaskStatus.ACTIVE)
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)

    async def get_page(self, *, limit: int = 10, offset: int = 0) -> Sequence[Task]:
        async with get_session() as session:
            stmt = (
                select(Task)
                .order_by(Task.created_at.desc(), Task.id.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def get_admin_task_data(self, task_id: int) -> dict[str, Any] | None:
        async with get_session() as session:
            stmt = (
                select(
                    Task.id.label("id"),
                    Task.title.label("title"),
                    Task.description.label("description"),
                    Task.note.label("note"),
                    Task.reward.label("reward"),
                    Task.max_completions.label("max_completions"),
                    Task.current_completions.label("current_completions"),
                    Task.status.label("status"),
                    Task.available_from.label("available_from"),
                    Task.available_until.label("available_until"),
                    Task.created_at.label("created_at"),
                    City.name.label("city_name"),
                    Shop.name.label("shop_name"),
                    Shop.address.label("shop_address"),
                )
                .select_from(Task)
                .outerjoin(City, City.id == Task.city_id)
                .outerjoin(Shop, Shop.id == Task.shop_id)
                .where(Task.id == task_id)
            )
            row = (await session.execute(stmt)).mappings().first()
            if row is None:
                return None
            data = dict(row)
            status = data.get("status")
            data["status"] = status.value if hasattr(status, "value") else str(status)
            return data

    async def get_available_for_user(
        self,
        *,
        city_id: int | None = None,
        shop_id: int | None = None,
        now: datetime | None = None,
    ) -> list[Task]:
        if now is None:
            now = datetime.utcnow()

        async with get_session() as session:
            conditions = [
                Task.status == TaskStatus.ACTIVE,
                Task.current_completions < Task.max_completions,
                (Task.available_from == None) | (Task.available_from <= now),
                (Task.available_until == None) | (Task.available_until >= now),
            ]

            if city_id is not None:
                conditions.append(Task.city_id == city_id)
            if shop_id is not None:
                conditions.append(Task.shop_id == shop_id)

            stmt = select(Task).where(and_(*conditions)).order_by(Task.id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(
        self,
        *,
        title: str,
        max_completions: int,
        reward: float | Decimal | None = None,
        description: str | None = None,
        note: str | None = None,
        city_id: int | None = None,
        shop_id: int | None = None,
        available_from: datetime | None = None,
        available_until: datetime | None = None,
        status: TaskStatus = TaskStatus.ACTIVE,
    ) -> Task:
        async with get_session() as session:
            final_reward: Decimal | float = 0
            if reward is not None:
                final_reward = reward
            elif shop_id is not None:
                shop = await session.get(Shop, shop_id)
                if shop is not None:
                    final_reward = shop.base_reward

            task = Task(
                title=title,
                description=description,
                note=note,
                city_id=city_id,
                shop_id=shop_id,
                reward=final_reward,
                max_completions=max_completions,
                current_completions=0,
                available_from=available_from,
                available_until=available_until,
                status=status,
                created_at=datetime.utcnow(),
            )
            session.add(task)
            await session.flush()
            await session.refresh(task)
            return task

    async def update(self, task_id: int, **fields: Any) -> Task | None:
        allowed_fields = {
            "title",
            "reward",
            "max_completions",
            "description",
            "note",
            "city_id",
            "shop_id",
            "available_from",
            "available_until",
            "status",
            "current_completions",
        }
        updates = {k: v for k, v in fields.items() if k in allowed_fields and v is not None}
        if not updates:
            return await self.get_by_id(task_id)

        async with get_session() as session:
            task = await session.get(Task, task_id)
            if task is None:
                return None
            for key, value in updates.items():
                setattr(task, key, value)
            await session.flush()
            await session.refresh(task)
            return task

    async def increment_completions(self, task_id: int) -> Task | None:
        async with get_session() as session:
            task = await session.get(Task, task_id)
            if task is None:
                return None
            task.current_completions += 1
            if task.current_completions >= task.max_completions:
                task.status = TaskStatus.COMPLETED
            await session.flush()
            await session.refresh(task)
            return task

    async def restart_task(self, task_id: int) -> Task | None:
        return await self.update(task_id, current_completions=0, status=TaskStatus.ACTIVE)

    async def set_status(self, task_id: int, status: TaskStatus) -> Task | None:
        async with get_session() as session:
            task = await session.get(Task, task_id)
            if task is None:
                return None
            task.status = status
            await session.flush()
            await session.refresh(task)
            return task

    async def delete(self, task_id: int) -> bool:
        async with get_session() as session:
            task = await session.get(Task, task_id)
            if task is None:
                return False
            await session.delete(task)
            await session.flush()
            return True
