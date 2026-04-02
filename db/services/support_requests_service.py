from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select, update

from db.database import get_session
from db.models import SupportRequest, SupportRequestStatus


class SupportRequestService:
    async def create(
        self,
        *,
        user_id: int | None,
        username: str | None,
        message_text: str,
    ) -> SupportRequest:
        async with get_session() as session:
            request = SupportRequest(
                user_id=user_id,
                username=username,
                message_text=message_text,
                status=SupportRequestStatus.OPEN,
            )
            session.add(request)
            await session.flush()
            await session.refresh(request)
            return request

    async def get_by_id(self, request_id: int) -> SupportRequest | None:
        async with get_session() as session:
            return await session.get(SupportRequest, request_id)

    async def get_recent(self, limit: int = 10, *, include_deleted: bool = False) -> list[SupportRequest]:
        async with get_session() as session:
            stmt = select(SupportRequest)
            if not include_deleted:
                stmt = stmt.where(SupportRequest.status != SupportRequestStatus.DELETED)
            stmt = stmt.order_by(SupportRequest.created_at.desc(), SupportRequest.id.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_page(self, *, limit: int = 10, offset: int = 0, include_deleted: bool = False) -> list[SupportRequest]:
        async with get_session() as session:
            stmt = select(SupportRequest)
            if not include_deleted:
                stmt = stmt.where(SupportRequest.status != SupportRequestStatus.DELETED)
            stmt = stmt.order_by(
                SupportRequest.is_viewed.asc(),
                SupportRequest.created_at.desc(),
                SupportRequest.id.desc(),
            ).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_all(self, *, include_deleted: bool = False) -> int:
        async with get_session() as session:
            stmt = select(func.count()).select_from(SupportRequest)
            if not include_deleted:
                stmt = stmt.where(SupportRequest.status != SupportRequestStatus.DELETED)
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)

    async def count_unseen(self) -> int:
        async with get_session() as session:
            stmt = (
                select(func.count())
                .select_from(SupportRequest)
                .where(SupportRequest.is_viewed.is_(False))
                .where(SupportRequest.status != SupportRequestStatus.DELETED)
            )
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)

    async def mark_all_viewed(self) -> None:
        async with get_session() as session:
            stmt = (
                update(SupportRequest)
                .where(SupportRequest.is_viewed.is_(False))
                .where(SupportRequest.status != SupportRequestStatus.DELETED)
                .values(is_viewed=True)
            )
            await session.execute(stmt)
            await session.flush()

    async def mark_viewed(self, request_id: int) -> SupportRequest | None:
        async with get_session() as session:
            request = await session.get(SupportRequest, request_id)
            if request is None:
                return None
            request.is_viewed = True
            await session.flush()
            await session.refresh(request)
            return request

    async def answer(self, request_id: int, *, admin_reply: str, answered_by: int | None) -> SupportRequest | None:
        async with get_session() as session:
            request = await session.get(SupportRequest, request_id)
            if request is None:
                return None
            request.admin_reply = admin_reply
            request.answered_by = answered_by
            request.replied_at = datetime.utcnow()
            request.status = SupportRequestStatus.ANSWERED
            request.is_viewed = True
            await session.flush()
            await session.refresh(request)
            return request

    async def delete(self, request_id: int) -> SupportRequest | None:
        async with get_session() as session:
            request = await session.get(SupportRequest, request_id)
            if request is None:
                return None
            request.status = SupportRequestStatus.DELETED
            request.is_viewed = True
            await session.flush()
            await session.refresh(request)
            return request

    async def get_user_history(self, user_id: int, *, limit: int = 20, offset: int = 0, include_deleted: bool = False) -> list[SupportRequest]:
        async with get_session() as session:
            stmt = select(SupportRequest).where(SupportRequest.user_id == user_id)
            if not include_deleted:
                stmt = stmt.where(SupportRequest.status != SupportRequestStatus.DELETED)
            stmt = stmt.order_by(SupportRequest.created_at.desc(), SupportRequest.id.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_user_history(self, user_id: int, *, include_deleted: bool = False) -> int:
        async with get_session() as session:
            stmt = select(func.count()).select_from(SupportRequest).where(SupportRequest.user_id == user_id)
            if not include_deleted:
                stmt = stmt.where(SupportRequest.status != SupportRequestStatus.DELETED)
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)
