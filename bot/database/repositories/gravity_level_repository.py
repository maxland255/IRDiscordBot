from datetime import datetime, UTC

from typing import Protocol, List, Union

from bot.database.schemas import GravityLevelSchema, GravityLevelUpdate, GravityLevelCreate
from bot.database.models import GravityLevel
from bot.exception import GravityLevelNotFound

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker


class GravityLevelRepository(Protocol):
    """
    Declare all methode available in the Gravity Level Repository.
    This is the unique API for all data sources.
    """

    async def get_all_gravity_level(self, guild_id: int) -> List[GravityLevelSchema]:
        """
        Get all Gravity Level data.
        :return:
        """
        ...

    async def get_gravity_level_by_id(self, gravity_level_id: int, raise_if_not_found: bool = False) -> Union[
        GravityLevelSchema, None]:
        """
        Get specific Gravity Level data.
        :param gravity_level_id:
        :param raise_if_not_found: Raise an exception if no Gravity Level found.
        :return:
        """
        ...

    async def create_gravity_level(self, gravity_level: GravityLevelCreate) -> GravityLevelSchema:
        """
        Create Gravity Level data.
        :param gravity_level:
        :return:
        """
        ...

    async def update_gravity_level(self, gravity_level: GravityLevelUpdate) -> GravityLevelSchema:
        """
        Update specific Gravity Level data.
        :param gravity_level:
        :return:
        """
        ...

    async def delete_gravity_level(self, gravity_level: GravityLevelSchema) -> None:
        """
        Soft delete specific Gravity Level data.
        :param gravity_level:
        :return:
        """
        ...

    async def delete_gravity_level_by_id(self, gravity_level_id: int) -> None:
        """
        Soft delete specific Gravity Level data.
        :param gravity_level_id:
        :return:
        """
        ...


class SQLAlchemyGravityLevelRepository(GravityLevelRepository):
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def get_all_gravity_level(self, guild_id: int) -> List[GravityLevelSchema]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(GravityLevel)
                .where(GravityLevel.deleted_at.is_(None))
                .where(GravityLevel.guild_id == guild_id)
            )

            db_gravity_levels = result.scalars().all()

            return [GravityLevelSchema.model_validate(db_gravity_level) for db_gravity_level in db_gravity_levels]

    async def get_gravity_level_by_id(self, gravity_level_id: int, raise_if_not_found: bool = False) -> Union[
        GravityLevelSchema, None]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(GravityLevel).where(GravityLevel.id == gravity_level_id)
            )

            db_gravity_level = result.scalar_one_or_none()

            if db_gravity_level is None:
                if raise_if_not_found:
                    raise GravityLevelNotFound(gravity_level_id)
                else:
                    return None

            return GravityLevelSchema.model_validate(db_gravity_level)

    async def create_gravity_level(self, gravity_level: GravityLevelCreate) -> GravityLevelSchema:
        async with self.session_factory() as session:
            db_gravity_level = GravityLevel(**gravity_level.model_dump())

            session.add(db_gravity_level)
            await session.commit()
            await session.refresh(db_gravity_level)

            return GravityLevelSchema.model_validate(db_gravity_level)

    async def update_gravity_level(self, gravity_level: GravityLevelUpdate) -> GravityLevelSchema:
        async with self.session_factory() as session:
            db_gravity_level = await session.get(GravityLevel, gravity_level.id)

            if db_gravity_level is None:
                raise GravityLevelNotFound(gravity_level)

            update_data = gravity_level.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_gravity_level, key, value)

            session.add(db_gravity_level)
            await session.commit()
            await session.refresh(db_gravity_level)

            return GravityLevelSchema.model_validate(db_gravity_level)

    async def delete_gravity_level(self, gravity_level: GravityLevelSchema) -> None:
        async with self.session_factory() as session:
            db_gravity_level = await session.get(GravityLevel, gravity_level.id)

            if db_gravity_level is None:
                raise GravityLevelNotFound(gravity_level)

            db_gravity_level.deleted_at = datetime.now(UTC)

            session.add(db_gravity_level)
            await session.commit()

    async def delete_gravity_level_by_id(self, gravity_level_id: int) -> None:
        async with self.session_factory() as session:
            db_gravity_level = await session.get(GravityLevel, gravity_level_id)

            if db_gravity_level is None:
                raise GravityLevelNotFound(gravity_level_id)

            db_gravity_level.deleted_at = datetime.now(UTC)

            session.add(db_gravity_level)
            await session.commit()
