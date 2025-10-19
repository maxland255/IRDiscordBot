from typing import Protocol, Optional
from abc import abstractmethod
from datetime import datetime, UTC, timedelta

from bot.database.schemas import RolePanelSchema, RolePanelCreate, RolePanelUpdate
from bot.database.models import RolePanel
from bot.exception import RolesPanelNotFound

from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import async_sessionmaker


class RolePanelRepository(Protocol):
    """
    Declare all methode available in the Role Panel Repository.
    This is the unique API for all data sources.
    """

    @abstractmethod
    async def get_all_roles_panel_by_guild_id(self, guild_id: int) -> list[RolePanelSchema]:
        """
        Get all roles panel by guild id.
        :param guild_id:
        :return:
        """
        ...

    @abstractmethod
    async def get_roles_panel_by_id(self, panel_id: int, raise_if_not_found: bool = False) -> Optional[RolePanelSchema]:
        """
        Get a roles panel by its id.
        :param panel_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def get_all_active_roles_panel(self) -> list[RolePanelSchema]:
        """
        Get all active roles panels.
        An active roles panel is a panel that contains a value in 'channel_id' and 'message_id'.
        A deleted panel with a value in 'channel_id' and 'message_id' is still considered as active but response with an error when trying to use it.
        :return:
        """
        ...

    @abstractmethod
    async def create_roles_panel(self, panel: RolePanelCreate) -> RolePanelSchema:
        """
        Create a roles panel.
        :param panel:
        :return:
        """
        ...

    @abstractmethod
    async def update_roles_panel(self, panel: RolePanelUpdate) -> RolePanelSchema:
        """
        Update a roles panel.
        :param panel:
        :return:
        """
        ...

    @abstractmethod
    async def remove_roles_panel(self, panel: RolePanelSchema) -> bool:
        """
        Remove a roles panel.
        :param panel:
        :return:
        """
        ...

    @abstractmethod
    async def delete_role_panel(self, panel_id: int) -> bool:
        """
        Delete a roles panel.
        :param panel_id:
        :return:
        """
        ...


class SQLAlchemyRolePanelRepository(RolePanelRepository):
    def __init__(self, session: async_sessionmaker):
        self.session = session

    async def get_all_roles_panel_by_guild_id(self, guild_id: int) -> list[RolePanelSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(RolePanel)
                .where(RolePanel.guild_id == guild_id)
                .where(RolePanel.deleted_at.is_(None))
                .options(selectinload(RolePanel.options))
            )

            db_role_panels = result.scalars().all()

            return [RolePanelSchema.model_validate(panel) for panel in db_role_panels]

    async def get_roles_panel_by_id(self, panel_id: int, raise_if_not_found: bool = False) -> Optional[RolePanelSchema]:
        async with self.session() as session:
            db_role_panel = await session.get(
                RolePanel,
                panel_id,
                options=[selectinload(RolePanel.options)],
            )

            if db_role_panel is None:
                if raise_if_not_found:
                    raise RolesPanelNotFound(panel_id)
                else:
                    return None

            return RolePanelSchema.model_validate(db_role_panel)

    async def get_all_active_roles_panel(self) -> list[RolePanelSchema]:
        async with self.session() as session:
            grace_period = datetime.now(UTC) - timedelta(weeks=2)

            result = await session.execute(
                select(RolePanel)
                .where(
                    RolePanel.channel_id.is_not(None),
                    RolePanel.message_id.is_not(None),
                    or_(
                        RolePanel.deleted_at.is_(None),
                        RolePanel.deleted_at > grace_period
                    )
                )
                .options(selectinload(RolePanel.options))
            )

            db_roles_panels = result.scalars().all()

            return [RolePanelSchema.model_validate(panel) for panel in db_roles_panels]

    async def create_roles_panel(self, panel: RolePanelCreate) -> RolePanelSchema:
        async with self.session() as session:
            db_role_panel = RolePanel(**panel.model_dump())

            session.add(db_role_panel)
            await session.commit()
            await session.refresh(db_role_panel)

            return await self.get_roles_panel_by_id(db_role_panel.id, raise_if_not_found=True)

    async def update_roles_panel(self, panel: RolePanelUpdate) -> RolePanelSchema:
        async with self.session() as session:
            db_role_panel = await session.get(
                RolePanel,
                panel.id,
                options=[selectinload(RolePanel.options)],
            )

            if db_role_panel is None or db_role_panel.deleted_at is not None:
                raise RolesPanelNotFound(panel)

            update_data = panel.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_role_panel, key, value)

            session.add(db_role_panel)
            await session.commit()
            await session.refresh(db_role_panel)

            return RolePanelSchema.model_validate(db_role_panel)

    async def remove_roles_panel(self, panel: RolePanelSchema) -> bool:
        async with self.session() as session:
            db_role_panel = await session.get(RolePanel, panel.id)

            if db_role_panel is None or db_role_panel.deleted_at is not None:
                return False

            db_role_panel.deleted_at = datetime.now(UTC)

            session.add(db_role_panel)
            await session.commit()

            return True

    async def delete_role_panel(self, panel_id: int) -> bool:
        async with self.session() as session:
            db_role_panel = await session.get(RolePanel, panel_id)

            if db_role_panel is None or db_role_panel.deleted_at is not None:
                return False

            db_role_panel.deleted_at = datetime.now(UTC)

            session.add(db_role_panel)
            await session.commit()

            return True
