from datetime import datetime
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_session
from db.models import User, ReferralSummary, UserStatus


class UserService:
    async def get_by_id(self, user_id: int) -> User | None:
        async with get_session() as session:
            return await session.get(User, user_id)

    async def get_by_username(self, username: str) -> User | None:
        async with get_session() as session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> Sequence[User]:
        async with get_session() as session:
            stmt = select(User).order_by(User.id)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def create(
        self,
        *,
        username: str,
        city_id: int | None = None,
        ref_parent_username: str | None = None,
        status: UserStatus = UserStatus.USER,
    ) -> User:
        async with get_session() as session:
            ref_parent_id: int | None = None

            if ref_parent_username is not None:
                stmt_parent = select(User).where(User.username == ref_parent_username)
                res_parent = await session.execute(stmt_parent)
                parent = res_parent.scalars().first()
                if parent:
                    ref_parent_id = parent.id

            user = User(
                username=username,
                city_id=city_id,
                ref_parent_id=ref_parent_id,
                status=status,
                created_at=datetime.utcnow(),
            )
            session.add(user)
            await session.flush()

            referral_summary = ReferralSummary(user_id=user.id)
            session.add(referral_summary)

            await session.flush()
            await session.refresh(user)
            return user

    async def update(
        self,
        username: str,
        *,
        new_username: str | None = None,
        city_id: int | None = None,
        ref_parent_username: str | None = None,
        status: UserStatus | None = None,
    ) -> User | None:
        async with get_session() as session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            user = result.scalars().first()
            if user is None:
                return None

            if new_username is not None:
                user.username = new_username
            if city_id is not None:
                user.city_id = city_id
            if ref_parent_username is not None:
                stmt_parent = select(User).where(
                    User.username == ref_parent_username
                )
                res_parent = await session.execute(stmt_parent)
                parent = res_parent.scalars().first()
                user.ref_parent_id = parent.id if parent else None
            if status is not None:
                user.status = status

            await session.flush()
            await session.refresh(user)
            return user

    async def change_balance(
        self,
        *,
        username: str,
        delta: int,
    ) -> User | None:
        async with get_session() as session:
            stmt = (
                select(User)
                .where(User.username == username)
                .with_for_update()
            )
            result = await session.execute(stmt)
            user: User | None = result.scalars().first()
            if user is None:
                return None

            user.balance += delta
            await session.flush()
            await session.refresh(user)
            return user

    async def delete(self, username: str) -> bool:
        async with get_session() as session:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            user = result.scalars().first()
            if user is None:
                return False

            await session.delete(user)
            await session.flush()
            return True

    async def change_balance_with_referrals(
        self,
        *,
        username: str,
        delta: int,
        level1_percent: float = 0.20,
        level2_percent: float = 0.05,
    ) -> User | None:
        if delta == 0:
            return await self.get_by_username(username)

        async with get_session() as session:
            # Лочим строку основного пользователя
            stmt_user = (
                select(User)
                .where(User.username == username)
                .with_for_update()
            )
            res_user = await session.execute(stmt_user)
            user: User | None = res_user.scalars().first()
            if user is None:
                return None

            # Начисляем основную сумму
            user.balance += delta

            # Считаем реферальные проценты
            level1_reward = 0
            level2_reward = 0

            if delta > 0:
                level1_reward = int(delta * level1_percent)
                level2_reward = int(delta * level2_percent)

            # LEVEL 1
            if user.ref_parent_id and level1_reward != 0:
                stmt_l1 = (
                    select(User)
                    .where(User.id == user.ref_parent_id)
                    .with_for_update()
                )
                res_l1 = await session.execute(stmt_l1)
                level1_user: User | None = res_l1.scalars().first()
                if level1_user:
                    level1_user.balance += level1_reward
                    # summary по 1 уровню
                    stmt_l1_sum = (
                        select(ReferralSummary)
                        .where(ReferralSummary.user_id == level1_user.id)
                        .with_for_update()
                    )
                    res_l1_sum = await session.execute(stmt_l1_sum)
                    l1_summary = res_l1_sum.scalars().first()
                    if l1_summary is None:
                        l1_summary = ReferralSummary(user_id=level1_user.id)
                        session.add(l1_summary)
                        await session.flush()

                    l1_summary.level1_earnings += level1_reward

                    # LEVEL 2
                    if level1_user.ref_parent_id and level2_reward != 0:
                        stmt_l2 = (
                            select(User)
                            .where(User.id == level1_user.ref_parent_id)
                            .with_for_update()
                        )
                        res_l2 = await session.execute(stmt_l2)
                        level2_user: User | None = res_l2.scalars().first()
                        if level2_user:
                            level2_user.balance += level2_reward

                            stmt_l2_sum = (
                                select(ReferralSummary)
                                .where(ReferralSummary.user_id == level2_user.id)
                                .with_for_update()
                            )
                            res_l2_sum = await session.execute(stmt_l2_sum)
                            l2_summary = res_l2_sum.scalars().first()
                            if l2_summary is None:
                                l2_summary = ReferralSummary(user_id=level2_user.id)
                                session.add(l2_summary)
                                await session.flush()

                            l2_summary.level2_earnings += level2_reward

            await session.flush()
            await session.refresh(user)
            return user

    async def increment_referral_counters_for_new_user(
            self,
            new_username: str,
    ) -> None:
        async with get_session() as session:
            stmt_user = select(User).where(User.username == new_username)
            res_user = await session.execute(stmt_user)
            user = res_user.scalars().first()
            if user is None or user.ref_parent_id is None:
                return

            # Level 1
            stmt_parent = select(User).where(User.id == user.ref_parent_id)
            res_parent = await session.execute(stmt_parent)
            parent = res_parent.scalars().first()
            if parent:
                stmt_parent_sum = select(ReferralSummary).where(
                    ReferralSummary.user_id == parent.id
                )
                res_parent_sum = await session.execute(stmt_parent_sum)
                parent_summary = res_parent_sum.scalars().first()
                if parent_summary is None:
                    parent_summary = ReferralSummary(user_id=parent.id)
                    session.add(parent_summary)
                    await session.flush()

                parent_summary.level1_count += 1

                # Level 2
                if parent.ref_parent_id:
                    stmt_grand = select(User).where(
                        User.id == parent.ref_parent_id
                    )
                    res_grand = await session.execute(stmt_grand)
                    grand = res_grand.scalars().first()
                    if grand:
                        stmt_grand_sum = select(ReferralSummary).where(
                            ReferralSummary.user_id == grand.id
                        )
                        res_grand_sum = await session.execute(stmt_grand_sum)
                        grand_summary = res_grand_sum.scalars().first()
                        if grand_summary is None:
                            grand_summary = ReferralSummary(user_id=grand.id)
                            session.add(grand_summary)
                            await session.flush()

                        grand_summary.level2_count += 1

            await session.flush()
