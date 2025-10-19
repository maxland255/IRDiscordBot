from abc import abstractmethod
from typing import Protocol, List, Union

from datetime import datetime, UTC

from bot.database.models import Infractions
from bot.database.schemas import InfractionsSchema, InfractionsCreate, InfractionsUpdate
from bot.exception import InfractionNotFound

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import async_sessionmaker


class InfractionsRepository(Protocol):
    """
    Declare all methode available in the Infraction Repository.
    This is the unique API for all data sources.
    """

    @abstractmethod
    async def get_all_infractions(self, guild_id: int) -> List[InfractionsSchema]:
        """
        Get all Infractions data.
        :param guild_id:
        :return:
        """
        ...

    @abstractmethod
    async def get_all_infractions_by_user(self, guild_id: int, user_id: int) -> List[InfractionsSchema]:
        """
        Get all Infractions data for a specific user.
        :param guild_id:
        :param user_id:
        :return:
        """
        ...

    @abstractmethod
    async def get_infraction_by_id(self, infraction_id: int,
                                   raise_if_not_found: bool = False) -> InfractionsSchema | None:
        """
        Get specific Infraction data.
        :param infraction_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def create_infraction(self, infraction: InfractionsCreate) -> InfractionsSchema:
        """
        Create Infraction data.
        :param infraction:
        :return:
        """
        ...

    @abstractmethod
    async def update_infraction(self, infraction: InfractionsUpdate) -> InfractionsSchema:
        """
        Update specific Infraction data.
        :param infraction:
        :return:
        """
        ...

    @abstractmethod
    async def delete_infraction_by_id(self, infraction_id: int) -> Union[InfractionsSchema, None]:
        """
        Delete a specific Infraction data.
        :param infraction_id:
        :return:
        """
        ...


class SQLAlchemyInfractionsRepository(InfractionsRepository):
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def get_all_infractions(self, guild_id: int) -> List[InfractionsSchema]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Infractions)
                .where(Infractions.guild_id == guild_id)
                .where(Infractions.deleted_at.is_(None))
                .options(selectinload(Infractions.gravity))
            )

            db_infractions = result.scalars().all()

            return [InfractionsSchema.model_validate(db_infraction) for db_infraction in db_infractions]

    async def get_all_infractions_by_user(self, guild_id: int, user_id: int) -> List[InfractionsSchema]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Infractions)
                .where(Infractions.guild_id == guild_id)
                .where(Infractions.user_id == user_id)
                .where(Infractions.deleted_at.is_(None))
                .options(selectinload(Infractions.gravity))
            )

            db_infractions = result.scalars().all()

            return [InfractionsSchema.model_validate(db_infraction) for db_infraction in db_infractions]

    async def get_infraction_by_id(self, infraction_id: int,
                                   raise_if_not_found: bool = False) -> InfractionsSchema | None:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Infractions)
                .where(Infractions.id == infraction_id)
                .options(selectinload(Infractions.gravity))
            )

            db_infractions = result.scalar_one_or_none()

            if db_infractions is None:
                if raise_if_not_found:
                    raise InfractionNotFound(infraction_id)
                else:
                    return None

            return InfractionsSchema.model_validate(db_infractions)

    async def create_infraction(self, infraction: InfractionsCreate) -> InfractionsSchema:
        async with self.session_factory() as session:
            db_infraction = Infractions(**infraction.model_dump())

            session.add(db_infraction)
            await session.commit()
            await session.refresh(db_infraction)

            return await self.get_infraction_by_id(db_infraction.id, raise_if_not_found=True)

    async def update_infraction(self, infraction: InfractionsUpdate) -> InfractionsSchema:
        async with self.session_factory() as session:
            db_infraction = await session.get(
                Infractions,
                infraction.id,
                options=[selectinload(Infractions.gravity)],
            )

            if db_infraction is None or db_infraction.deleted_at is not None:
                raise InfractionNotFound(infraction)

            updated_data = infraction.model_dump(exclude_unset=True)

            for key, value in updated_data.items():
                setattr(db_infraction, key, value)

            session.add(db_infraction)
            await session.commit()
            await session.refresh(db_infraction)

            return InfractionsSchema.model_validate(db_infraction)

    async def delete_infraction_by_id(self, infraction_id: int) -> Union[InfractionsSchema, None]:
        async with self.session_factory() as session:
            db_infraction = await session.get(Infractions, infraction_id)

            if db_infraction is None or db_infraction.deleted_at is not None:
                raise InfractionNotFound(infraction_id)

            db_infraction.deleted_at = datetime.now(UTC)

            session.add(db_infraction)
            await session.commit()
