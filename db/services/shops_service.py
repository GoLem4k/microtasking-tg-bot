from decimal import Decimal
from typing import Any

from sqlalchemy import select

from db.database import get_session
from db.models import Shop


class ShopService:
    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().lower()

    async def get_by_id(self, shop_id: int) -> Shop | None:
        async with get_session() as session:
            return await session.get(Shop, shop_id)

    async def get_by_name(self, name: str, city_id: int | None = None) -> Shop | None:
        normalized = self._normalize_name(name)
        async with get_session() as session:
            stmt = select(Shop).where(Shop.name == normalized)
            if city_id is not None:
                stmt = stmt.where(Shop.city_id == city_id)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> list[Shop]:
        async with get_session() as session:
            stmt = select(Shop).order_by(Shop.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def get_by_city(self, city_id: int) -> list[Shop]:
        async with get_session() as session:
            stmt = (
                select(Shop)
                .where(Shop.city_id == city_id)
                .order_by(Shop.name)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(
        self,
        *,
        name: str,
        city_id: int,
        address: str | None = None,
        base_reward: float | Decimal = 0,
    ) -> Shop:
        normalized = self._normalize_name(name)

        existing = await self.get_by_name(normalized, city_id=city_id)
        if existing is not None:
            return existing

        async with get_session() as session:
            shop = Shop(
                name=normalized,
                city_id=city_id,
                address=address,
                base_reward=base_reward,
            )
            session.add(shop)
            await session.flush()
            await session.refresh(shop)
            return shop

    async def update(
        self,
        shop_id: int,
        *,
        name: str | None = None,
        address: str | None = None,
        base_reward: float | Decimal | None = None,
    ) -> Shop | None:
        async with get_session() as session:
            shop = await session.get(Shop, shop_id)
            if shop is None:
                return None

            updates: dict[str, Any] = {}

            if name is not None:
                updates["name"] = self._normalize_name(name)
            if address is not None:
                updates["address"] = address
            if base_reward is not None:
                updates["base_reward"] = base_reward

            for key, value in updates.items():
                setattr(shop, key, value)

            await session.flush()
            await session.refresh(shop)
            return shop

    async def delete_by_id(self, shop_id: int) -> bool:
        async with get_session() as session:
            shop = await session.get(Shop, shop_id)
            if shop is None:
                return False
            await session.delete(shop)
            await session.flush()
            return True

    async def delete_by_name(
        self,
        *,
        name: str,
        city_id: int | None = None,
    ) -> bool:
        normalized = self._normalize_name(name)
        async with get_session() as session:
            stmt = select(Shop).where(Shop.name == normalized)
            if city_id is not None:
                stmt = stmt.where(Shop.city_id == city_id)

            result = await session.execute(stmt)
            shop = result.scalars().first()
            if shop is None:
                return False

            await session.delete(shop)
            await session.flush()
            return True
