from __future__ import annotations

from datetime import datetime
from typing import Sequence

from sqlalchemy import func, select

from db.database import get_session
from db.models.withdraw_request import WithdrawRequest, WithdrawRequestStatus


class WithdrawRequestService:
    async def create(
        self,
        *,
        user_id: int | None,
        username: str | None,
        method: str,
        amount: int,
        requisites: str | None = None,
        currency: str | None = None,
    ) -> WithdrawRequest:
        async with get_session() as session:
            item = WithdrawRequest(
                user_id=user_id,
                username=username,
                method=method,
                amount=amount,
                requisites=requisites,
                currency=currency,
            )
            session.add(item)
            await session.flush()
            await session.refresh(item)
            return item

    async def get_by_id(self, request_id: int) -> WithdrawRequest | None:
        async with get_session() as session:
            return await session.get(WithdrawRequest, request_id)

    async def get_page(self, *, limit: int = 10, offset: int = 0) -> Sequence[WithdrawRequest]:
        async with get_session() as session:
            stmt = (
                select(WithdrawRequest)
                .order_by(WithdrawRequest.created_at.desc(), WithdrawRequest.id.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return result.scalars().all()

    async def count_all(self) -> int:
        async with get_session() as session:
            stmt = select(func.count()).select_from(WithdrawRequest)
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)

    async def count_pending(self) -> int:
        return await self.count_by_status(WithdrawRequestStatus.PENDING)

    async def count_by_status(self, status: WithdrawRequestStatus) -> int:
        async with get_session() as session:
            stmt = select(func.count()).select_from(WithdrawRequest).where(WithdrawRequest.status == status)
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)

    async def approve(self, request_id: int, *, admin_comment: str | None = None) -> WithdrawRequest | None:
        async with get_session() as session:
            item = await session.get(WithdrawRequest, request_id)
            if item is None:
                return None
            item.status = WithdrawRequestStatus.APPROVED
            item.admin_comment = admin_comment
            item.processed_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            await session.flush()
            await session.refresh(item)
            return item

    async def reject(self, request_id: int, *, admin_comment: str | None = None) -> WithdrawRequest | None:
        async with get_session() as session:
            item = await session.get(WithdrawRequest, request_id)
            if item is None:
                return None
            item.status = WithdrawRequestStatus.REJECTED
            item.admin_comment = admin_comment
            item.processed_at = datetime.utcnow()
            item.updated_at = datetime.utcnow()
            await session.flush()
            await session.refresh(item)
            return item
