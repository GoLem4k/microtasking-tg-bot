from __future__ import annotations

from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import func, select

from db.database import get_session
from db.models import SubmissionStatus, Task, TaskSubmission, User


class TaskSubmissionService:
    async def get_by_id(self, submission_id: int) -> TaskSubmission | None:
        async with get_session() as session:
            return await session.get(TaskSubmission, submission_id)

    async def count_pending(self) -> int:
        async with get_session() as session:
            stmt = select(func.count()).select_from(TaskSubmission).where(TaskSubmission.status == SubmissionStatus.PENDING)
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)

    async def get_pending_page(self, *, limit: int = 10, offset: int = 0) -> list[dict[str, Any]]:
        async with get_session() as session:
            stmt = (
                select(
                    TaskSubmission.id.label("id"),
                    TaskSubmission.user_id.label("user_id"),
                    TaskSubmission.task_id.label("task_id"),
                    TaskSubmission.screenshot_id.label("screenshot_id"),
                    TaskSubmission.status.label("status"),
                    TaskSubmission.created_at.label("created_at"),
                    User.username.label("username"),
                    Task.title.label("task_title"),
                    Task.reward.label("reward"),
                )
                .select_from(TaskSubmission)
                .outerjoin(User, User.id == TaskSubmission.user_id)
                .outerjoin(Task, Task.id == TaskSubmission.task_id)
                .where(TaskSubmission.status == SubmissionStatus.PENDING)
                .order_by(TaskSubmission.created_at.asc(), TaskSubmission.id.asc())
                .limit(limit)
                .offset(offset)
            )
            rows = (await session.execute(stmt)).mappings().all()
            return [self._normalize_row(dict(row)) for row in rows]

    async def get_admin_submission_data(self, submission_id: int) -> dict[str, Any] | None:
        async with get_session() as session:
            stmt = (
                select(
                    TaskSubmission.id.label("id"),
                    TaskSubmission.user_id.label("user_id"),
                    TaskSubmission.task_id.label("task_id"),
                    TaskSubmission.screenshot_id.label("screenshot_id"),
                    TaskSubmission.status.label("status"),
                    TaskSubmission.created_at.label("created_at"),
                    TaskSubmission.updated_at.label("updated_at"),
                    User.username.label("username"),
                    Task.title.label("task_title"),
                    Task.reward.label("reward"),
                )
                .select_from(TaskSubmission)
                .outerjoin(User, User.id == TaskSubmission.user_id)
                .outerjoin(Task, Task.id == TaskSubmission.task_id)
                .where(TaskSubmission.id == submission_id)
            )
            row = (await session.execute(stmt)).mappings().first()
            if row is None:
                return None
            return self._normalize_row(dict(row))

    @staticmethod
    def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        status = row.get("status")
        row["status"] = status.value if hasattr(status, "value") else str(status)
        reward = row.get("reward")
        if reward is None:
            row["reward"] = 0
        else:
            row["reward"] = int(reward)
        row["username"] = row.get("username") or "без username"
        return row

    async def get_all_for_user(self, username: str) -> Sequence[TaskSubmission]:
        async with get_session() as session:
            stmt_user = select(User).where(User.username == username)
            res_user = await session.execute(stmt_user)
            user = res_user.scalars().first()
            if user is None:
                return []
            stmt = (
                select(TaskSubmission)
                .where(TaskSubmission.user_id == user.id)
                .order_by(TaskSubmission.created_at.desc())
            )
            res = await session.execute(stmt)
            return res.scalars().all()

    async def get_active_for_user(self, username: str) -> Sequence[TaskSubmission]:
        async with get_session() as session:
            stmt_user = select(User).where(User.username == username)
            res_user = await session.execute(stmt_user)
            user = res_user.scalars().first()
            if user is None:
                return []
            stmt = (
                select(TaskSubmission)
                .where(
                    TaskSubmission.user_id == user.id,
                    TaskSubmission.status.in_([SubmissionStatus.IN_PROGRESS, SubmissionStatus.PENDING]),
                )
                .order_by(TaskSubmission.created_at.desc())
            )
            res = await session.execute(stmt)
            return res.scalars().all()

    async def create(self, *, username: str, task_id: int, screenshot_id: str | None = None) -> TaskSubmission | None:
        async with get_session() as session:
            stmt_user = select(User).where(User.username == username)
            res_user = await session.execute(stmt_user)
            user = res_user.scalars().first()
            if user is None:
                return None
            task = await session.get(Task, task_id)
            if task is None:
                return None
            submission = TaskSubmission(
                user_id=user.id,
                task_id=task.id,
                screenshot_id=screenshot_id,
                status=SubmissionStatus.IN_PROGRESS,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            session.add(submission)
            await session.flush()
            await session.refresh(submission)
            return submission

    async def set_status(self, submission_id: int, status: SubmissionStatus) -> TaskSubmission | None:
        async with get_session() as session:
            submission = await session.get(TaskSubmission, submission_id)
            if submission is None:
                return None
            submission.status = status
            submission.updated_at = datetime.utcnow()
            await session.flush()
            await session.refresh(submission)
            return submission

    async def delete(self, submission_id: int) -> bool:
        async with get_session() as session:
            submission = await session.get(TaskSubmission, submission_id)
            if submission is None:
                return False
            await session.delete(submission)
            await session.flush()
            return True

    async def update_screenshot(self, submission_id: int, screenshot_id: str) -> TaskSubmission | None:
        async with get_session() as session:
            submission = await session.get(TaskSubmission, submission_id)
            if submission is None:
                return None
            submission.screenshot_id = screenshot_id
            submission.updated_at = datetime.utcnow()
            await session.flush()
            await session.refresh(submission)
            return submission

    async def set_screenshot_and_status(self, submission_id: int, *, screenshot_id: str, status: SubmissionStatus | None = None) -> TaskSubmission | None:
        async with get_session() as session:
            submission = await session.get(TaskSubmission, submission_id)
            if submission is None:
                return None
            submission.screenshot_id = screenshot_id
            if status is not None:
                submission.status = status
            submission.updated_at = datetime.utcnow()
            await session.flush()
            await session.refresh(submission)
            return submission
