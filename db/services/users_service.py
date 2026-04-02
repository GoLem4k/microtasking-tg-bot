from __future__ import annotations

from decimal import Decimal
from typing import Any, Sequence

from sqlalchemy import case, func, select

from db.database import get_session
from db.models import (
    ReferralSummary,
    SubmissionStatus,
    Task,
    TaskSubmission,
    User,
    UserStatus,
)


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

    async def get_all_active_recipients(self) -> Sequence[User]:
        async with get_session() as session:
            stmt = select(User).where(User.status != UserStatus.BAN).order_by(User.id)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def can_receive_bot_messages(self, user_id: int) -> bool:
        async with get_session() as session:
            stmt = select(User.status).where(User.id == user_id)
            result = await session.execute(stmt)
            status = result.scalar_one_or_none()
            return status is not None and status != UserStatus.BAN

    async def is_banned(self, user_id: int) -> bool:
        async with get_session() as session:
            stmt = select(User.status).where(User.id == user_id)
            result = await session.execute(stmt)
            status = result.scalar_one_or_none()
            return status == UserStatus.BAN

    async def get_admin_users(self) -> Sequence[User]:
        async with get_session() as session:
            stmt = select(User).where(User.status == UserStatus.ADMIN).order_by(User.id)
            result = await session.execute(stmt)
            return result.scalars().all()

    async def count_users(self) -> int:
        async with get_session() as session:
            stmt = select(func.count()).select_from(User)
            result = await session.execute(stmt)
            return int(result.scalar_one() or 0)

    async def get_users_page(self, *, limit: int = 10, offset: int = 0) -> Sequence[User]:
        async with get_session() as session:
            stmt = (
                select(User)
                .order_by(User.created_at.desc(), User.id.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(stmt)
            return result.scalars().all()


    async def create(
        self,
        *,
        user_id: int,
        username: str | None,
        city_id: int | None = None,
        ref_parent_id: int | None = None,
        ref_parent_username: str | None = None,
        status: UserStatus = UserStatus.USER,
    ) -> tuple[User, bool]:
        async with get_session() as session:
            stmt_existing = select(User).where(User.id == user_id)
            result_existing = await session.execute(stmt_existing)
            existing = result_existing.scalars().first()

            if existing is not None:
                return existing, False

            resolved_ref_parent_id = ref_parent_id

            if resolved_ref_parent_id == user_id:
                resolved_ref_parent_id = None

            if resolved_ref_parent_id is not None:
                stmt_parent_by_id = select(User).where(User.id == resolved_ref_parent_id)
                res_parent_by_id = await session.execute(stmt_parent_by_id)
                parent_by_id = res_parent_by_id.scalars().first()

                if parent_by_id is None:
                    resolved_ref_parent_id = None

            if resolved_ref_parent_id is None and ref_parent_username is not None:
                stmt_parent = select(User).where(User.username == ref_parent_username)
                res_parent = await session.execute(stmt_parent)
                parent = res_parent.scalars().first()

                if parent and parent.id != user_id:
                    resolved_ref_parent_id = parent.id

            user = User(
                id=user_id,
                username=username,
                city_id=city_id,
                ref_parent_id=resolved_ref_parent_id,
                status=status,
            )
            session.add(user)
            await session.flush()

            referral_summary = ReferralSummary(user_id=user.id)
            session.add(referral_summary)

            await session.flush()
            await session.refresh(user)
            return user, True

    async def get_referral_summary(self, user_id: int) -> ReferralSummary | None:
        async with get_session() as session:
            stmt = select(ReferralSummary).where(ReferralSummary.user_id == user_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_profile_data(self, user_id: int) -> dict[str, Any] | None:
        async with get_session() as session:
            user = await session.get(User, user_id)
            if user is None:
                return None

            task_stats_sq = (
                select(
                    TaskSubmission.user_id.label("user_id"),
                    func.sum(
                        case(
                            (TaskSubmission.status == SubmissionStatus.APPROVED, 1),
                            else_=0,
                        )
                    ).label("approved_count"),
                    func.sum(
                        case(
                            (TaskSubmission.status == SubmissionStatus.PENDING, 1),
                            else_=0,
                        )
                    ).label("pending_count"),
                    func.sum(
                        case(
                            (TaskSubmission.status == SubmissionStatus.IN_PROGRESS, 1),
                            else_=0,
                        )
                    ).label("unfinished_count"),
                    func.sum(
                        case(
                            (TaskSubmission.status == SubmissionStatus.APPROVED, Task.reward),
                            else_=0,
                        )
                    ).label("task_earnings"),
                )
                .select_from(TaskSubmission)
                .outerjoin(Task, Task.id == TaskSubmission.task_id)
                .group_by(TaskSubmission.user_id)
                .subquery()
            )

            referral_sq = (
                select(
                    ReferralSummary.user_id.label("user_id"),
                    ReferralSummary.level1_count.label("level1_count"),
                    ReferralSummary.level2_count.label("level2_count"),
                    (ReferralSummary.level1_count + ReferralSummary.level2_count).label(
                        "total_referrals"
                    ),
                    ReferralSummary.level1_earnings.label("level1_earnings"),
                    ReferralSummary.level2_earnings.label("level2_earnings"),
                    (
                        ReferralSummary.level1_earnings + ReferralSummary.level2_earnings
                    ).label("total_referral_earnings"),
                )
                .select_from(ReferralSummary)
                .subquery()
            )

            stmt = (
                select(
                    User.id.label("user_id"),
                    User.username.label("username"),
                    User.status.label("status"),
                    User.created_at.label("created_at"),
                    User.balance.label("balance"),
                    func.coalesce(task_stats_sq.c.approved_count, 0).label(
                        "approved_count"
                    ),
                    func.coalesce(task_stats_sq.c.pending_count, 0).label(
                        "pending_count"
                    ),
                    func.coalesce(task_stats_sq.c.unfinished_count, 0).label(
                        "unfinished_count"
                    ),
                    func.coalesce(task_stats_sq.c.task_earnings, 0).label(
                        "task_earnings"
                    ),
                    func.coalesce(referral_sq.c.level1_count, 0).label("level1_count"),
                    func.coalesce(referral_sq.c.level2_count, 0).label("level2_count"),
                    func.coalesce(referral_sq.c.total_referrals, 0).label(
                        "total_referrals"
                    ),
                    func.coalesce(referral_sq.c.level1_earnings, 0).label(
                        "level1_earnings"
                    ),
                    func.coalesce(referral_sq.c.level2_earnings, 0).label(
                        "level2_earnings"
                    ),
                    func.coalesce(referral_sq.c.total_referral_earnings, 0).label(
                        "total_referral_earnings"
                    ),
                )
                .select_from(User)
                .outerjoin(task_stats_sq, task_stats_sq.c.user_id == User.id)
                .outerjoin(referral_sq, referral_sq.c.user_id == User.id)
                .order_by(User.id)
            )

            rows = (await session.execute(stmt)).mappings().all()
            if not rows:
                return None

            all_profiles = [self._normalize_profile_row(dict(row)) for row in rows]
            current_profile = next(
                (profile for profile in all_profiles if profile["user_id"] == user_id),
                None,
            )
            if current_profile is None:
                return None

            current_profile["rank_by_task_earnings"] = self._build_dense_ranks(
                all_profiles,
                key="task_earnings",
            ).get(user_id, 1)
            current_profile["rank_by_referrals"] = self._build_dense_ranks(
                all_profiles,
                key="total_referrals",
            ).get(user_id, 1)
            current_profile["rank_by_referral_earnings"] = self._build_dense_ranks(
                all_profiles,
                key="total_referral_earnings",
            ).get(user_id, 1)

            return current_profile

    @staticmethod
    def _normalize_profile_row(row: dict[str, Any]) -> dict[str, Any]:
        numeric_fields = [
            "balance",
            "approved_count",
            "pending_count",
            "unfinished_count",
            "task_earnings",
            "level1_count",
            "level2_count",
            "total_referrals",
            "level1_earnings",
            "level2_earnings",
            "total_referral_earnings",
        ]

        normalized = dict(row)
        for field in numeric_fields:
            value = normalized.get(field, 0)
            if value is None:
                normalized[field] = 0
            elif isinstance(value, Decimal):
                normalized[field] = value
            else:
                normalized[field] = int(value)

        return normalized

    @staticmethod
    def _build_dense_ranks(
        profiles: list[dict[str, Any]],
        *,
        key: str,
    ) -> dict[int, int]:
        def ranking_sort_key(profile: dict[str, Any]) -> tuple[float, int]:
            value = profile[key]
            if isinstance(value, Decimal):
                sortable_value = float(value)
            else:
                sortable_value = float(value or 0)
            return (-sortable_value, profile["user_id"])

        sorted_profiles = sorted(profiles, key=ranking_sort_key)

        ranks: dict[int, int] = {}
        last_value: Any = None
        current_rank = 0

        for profile in sorted_profiles:
            value = profile[key]
            if last_value is None or value != last_value:
                current_rank += 1
                last_value = value
            ranks[profile["user_id"]] = current_rank

        return ranks

    async def update_username(
        self,
        user_id: int,
        username: str | None,
    ) -> User | None:
        async with get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if user is None:
                return None

            user.username = username
            await session.flush()
            await session.refresh(user)
            return user

    async def update(
        self,
        user_id: int,
        *,
        city_id: int | None = None,
        ref_parent_id: str | None = None,
        status: UserStatus | None = None,
    ) -> User | None:
        async with get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if user is None:
                return None

            if city_id is not None:
                user.city_id = city_id

            if ref_parent_id is not None:
                stmt_parent = select(User).where(User.id == ref_parent_id)
                res_parent = await session.execute(stmt_parent)
                parent = res_parent.scalars().first()
                user.ref_parent_id = parent.id if parent else None

            if status is not None:
                user.status = status

            await session.flush()
            await session.refresh(user)
            return user

    async def delete(self, user_id: int) -> bool:
        async with get_session() as session:
            stmt = select(User).where(User.id == user_id)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if user is None:
                return False

            await session.delete(user)
            await session.flush()
            return True

    async def change_balance(
        self,
        *,
        user_id: int,
        delta: int,
    ) -> User | None:
        async with get_session() as session:
            stmt = select(User).where(User.id == user_id).with_for_update()
            result = await session.execute(stmt)
            user = result.scalars().first()

            if user is None:
                return None

            user.balance += delta
            await session.flush()
            await session.refresh(user)
            return user

    async def change_balance_with_referrals(
        self,
        *,
        user_id: int,
        delta: int,
        level1_percent: float = 0.20,
        level2_percent: float = 0.05,
    ) -> User | None:
        if delta == 0:
            return await self.get_by_id(user_id)

        async with get_session() as session:
            stmt_user = select(User).where(User.id == user_id).with_for_update()
            res_user = await session.execute(stmt_user)
            user = res_user.scalars().first()

            if user is None:
                return None

            user.balance += delta

            level1_reward = 0
            level2_reward = 0

            if delta > 0:
                level1_reward = int(delta * level1_percent)
                level2_reward = int(delta * level2_percent)

            if user.ref_parent_id and level1_reward != 0:
                stmt_l1 = select(User).where(User.id == user.ref_parent_id).with_for_update()
                res_l1 = await session.execute(stmt_l1)
                level1_user = res_l1.scalars().first()

                if level1_user:
                    level1_user.balance += level1_reward

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

                    if level1_user.ref_parent_id and level2_reward != 0:
                        stmt_l2 = (
                            select(User)
                            .where(User.id == level1_user.ref_parent_id)
                            .with_for_update()
                        )
                        res_l2 = await session.execute(stmt_l2)
                        level2_user = res_l2.scalars().first()

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

    async def increment_referral_counters_for_new_user(self, new_user_id: int) -> None:
        async with get_session() as session:
            stmt_user = select(User).where(User.id == new_user_id)
            res_user = await session.execute(stmt_user)
            user = res_user.scalars().first()

            if user is None or user.ref_parent_id is None:
                return

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

                if parent.ref_parent_id:
                    stmt_grand = select(User).where(User.id == parent.ref_parent_id)
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
