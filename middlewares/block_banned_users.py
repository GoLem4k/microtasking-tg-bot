from __future__ import annotations

from aiogram import BaseMiddleware

from db.models import UserStatus
from db.services.users_service import UserService


class BlockBannedUsersMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        super().__init__()
        self.user_service = UserService()

    async def __call__(self, handler, event, data):
        from_user = getattr(event, "from_user", None)
        if from_user is None:
            return await handler(event, data)

        user = await self.user_service.get_by_id(from_user.id)
        if user is not None and user.status == UserStatus.BAN:
            return

        return await handler(event, data)
