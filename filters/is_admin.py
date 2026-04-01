# db/services/users_service.py

from db.database import get_session
from db.models import User, UserStatus
from sqlalchemy import select


async def is_admin(user_id: int) -> bool:
  
    async with get_session() as session:
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user is None:
            print(f"[DEBUG] Пользователь с id={user_id} не найден.")
            return False

        is_admin_flag = user.status == UserStatus.ADMIN
        print(f"[DEBUG] Проверка админа для user_id={user_id}: {is_admin_flag}")
        return is_admin_flag