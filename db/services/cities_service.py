from sqlalchemy import select

from db.database import get_session
from db.models import City


class CityService:
    @staticmethod
    def _normalize_name(name: str) -> str:
        return name.strip().lower()

    async def get_by_id(self, city_id: int) -> City | None:
        async with get_session() as session:
            return await session.get(City, city_id)

    async def get_by_name(self, name: str) -> City | None:
        normalized = self._normalize_name(name)
        async with get_session() as session:
            stmt = select(City).where(City.name == normalized)
            result = await session.execute(stmt)
            return result.scalars().first()

    async def get_all(self) -> list[City]:
        async with get_session() as session:
            stmt = select(City).order_by(City.name)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    async def create(self, name: str) -> City:
        normalized = self._normalize_name(name)
        async with get_session() as session:
            city = City(name=normalized)
            session.add(city)
            await session.flush()
            await session.refresh(city)
            return city

    async def rename(self, old_name: str, new_name: str) -> City | None:
        old_normalized = self._normalize_name(old_name)
        new_normalized = self._normalize_name(new_name)

        async with get_session() as session:
            stmt = select(City).where(City.name == old_normalized)
            result = await session.execute(stmt)
            city = result.scalars().first()
            if city is None:
                return None

            city.name = new_normalized
            await session.flush()
            await session.refresh(city)
            return city

    async def delete_by_name(self, name: str) -> bool:
        normalized = self._normalize_name(name)
        async with get_session() as session:
            stmt = select(City).where(City.name == normalized)
            result = await session.execute(stmt)
            city = result.scalars().first()
            if city is None:
                return False
            await session.delete(city)
            await session.flush()
            return True
