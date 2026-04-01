from sqlalchemy import select, func, update

from db.database import get_session
from db.models import SupportRequest


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
            )
            session.add(request)
            await session.flush()
            await session.refresh(request)
            return request

    async def get_recent(self, limit: int = 10) -> list[SupportRequest]:
        async with get_session() as session:
            stmt = (
                select(SupportRequest)
                .order_by(SupportRequest.created_at.desc(), SupportRequest.id.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def count_unseen(self) -> int:
        async with get_session() as session:
            stmt = select(func.count()).select_from(SupportRequest).where(SupportRequest.is_viewed.is_(False))
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)

    async def mark_all_viewed(self) -> None:
        async with get_session() as session:
            stmt = update(SupportRequest).where(SupportRequest.is_viewed.is_(False)).values(is_viewed=True)
            await session.execute(stmt)
            await session.flush()
