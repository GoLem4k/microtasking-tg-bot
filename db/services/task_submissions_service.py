from datetime import datetime
from typing import Sequence

from sqlalchemy import select

from db.database import get_session
from db.models import (
    TaskSubmission,
    SubmissionStatus,
    User,
    Task,
)


class TaskSubmissionService:
    async def get_by_id(self, submission_id: int) -> TaskSubmission | None:
        async with get_session() as session:
            return await session.get(TaskSubmission, submission_id)

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
        """
        Сабмишены пользователя в статусах IN_PROGRESS или PENDING.
        """
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
                    TaskSubmission.status.in_(
                        [SubmissionStatus.IN_PROGRESS, SubmissionStatus.PENDING]
                    ),
                )
                .order_by(TaskSubmission.created_at.desc())
            )
            res = await session.execute(stmt)
            return res.scalars().all()

    async def create(
        self,
        *,
        username: str,
        task_id: int,
        screenshot_id: str | None = None, # Telegram file_id
    ) -> TaskSubmission | None:
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

    async def set_status(
        self,
        submission_id: int,
        status: SubmissionStatus,
    ) -> TaskSubmission | None:
        """
        Меняет статус сабмишена (без денег и лимитов задач).
        """
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

    async def update_screenshot(
            self,
            submission_id: int,
            screenshot_id: str,
    ) -> TaskSubmission | None:
        async with get_session() as session:
            submission = await session.get(TaskSubmission, submission_id)
            if submission is None:
                return None

            submission.screenshot_id = screenshot_id
            submission.updated_at = datetime.utcnow()

            await session.flush()
            await session.refresh(submission)
            return submission

    async def set_screenshot_and_status(
            self,
            submission_id: int,
            *,
            screenshot_id: str,
            status: SubmissionStatus | None = None,
    ) -> TaskSubmission | None:
        """
        Обновить screenshot_id и статус
        """
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
