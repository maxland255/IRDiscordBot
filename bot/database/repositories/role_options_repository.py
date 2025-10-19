from typing import Protocol, Optional
from abc import abstractmethod

from bot.database.schemas import RoleOptionsSchema, RoleOptionsCreate, RoleOptionsUpdate
from bot.database.models import RoleOptions
from bot.exception import RoleOptionsNotFound

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker


class RoleOptionsRepository(Protocol):
    """
    Declare all methode available in the Role Options Repository.
    This is the unique API for all data sources.
    """

    @abstractmethod
    async def get_all_role_options_by_panel_id(self, panel_id: int) -> list[RoleOptionsSchema]:
        """
        Get all role options by panel id.
        :param panel_id:
        :return:
        """
        ...

    @abstractmethod
    async def get_role_options_by_id(self, option_id: int, raise_if_not_found: bool = False) -> Optional[
        RoleOptionsSchema]:
        """
        Get a role option by its id.
        :param option_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def create_role_options(self, role_option: RoleOptionsCreate) -> RoleOptionsSchema:
        """
        Create a role option.
        :param role_option:
        :return:
        """
        ...

    @abstractmethod
    async def update_role_options(self, role_option: RoleOptionsUpdate) -> RoleOptionsSchema:
        """
        Update a role option.
        :param role_option:
        :return:
        """
        ...

    @abstractmethod
    async def delete_role_options(self, option_id: int) -> bool:
        """
        Delete a role option.
        :param option_id:
        :return:
        """
        ...


class SQLAlchemyRoleOptionsRepository(RoleOptionsRepository):
    def __init__(self, session: async_sessionmaker):
        self.session = session

    async def get_all_role_options_by_panel_id(self, panel_id: int) -> list[RoleOptionsSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(RoleOptions)
                .where(RoleOptions.panel_id == panel_id)
            )

            db_role_options = result.scalars().all()

            return [RoleOptionsSchema.model_validate(role_option) for role_option in db_role_options]

    async def get_role_options_by_id(self, option_id: int, raise_if_not_found: bool = False) -> Optional[
        RoleOptionsSchema]:
        async with self.session() as session:
            db_role_options = await session.get(
                RoleOptions,
                option_id,
            )

            if db_role_options is None:
                if raise_if_not_found:
                    raise RoleOptionsNotFound(option_id)
                else:
                    return None

            return RoleOptionsSchema.model_validate(db_role_options)

    async def create_role_options(self, role_option: RoleOptionsCreate) -> RoleOptionsSchema:
        async with self.session() as session:
            db_role_option = RoleOptions(**role_option.model_dump())

            session.add(db_role_option)
            await session.commit()
            await session.refresh(db_role_option)

            return RoleOptionsSchema.model_validate(db_role_option)

    async def update_role_options(self, role_option: RoleOptionsUpdate) -> RoleOptionsSchema:
        async with self.session() as session:
            db_role_options = await session.get(
                RoleOptions,
                role_option.id,
            )

            if db_role_options is None:
                raise RoleOptionsNotFound(role_option.id)

            update_data = role_option.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_role_options, key, value)

            session.add(db_role_options)
            await session.commit()
            await session.refresh(db_role_options)

            return RoleOptionsSchema.model_validate(db_role_options)

    async def delete_role_options(self, option_id: int) -> bool:
        async with self.session() as session:
            db_role_options = await session.get(RoleOptions, option_id)

            if db_role_options is None:
                return False

            await session.delete(db_role_options)
            await session.commit()

            return True
