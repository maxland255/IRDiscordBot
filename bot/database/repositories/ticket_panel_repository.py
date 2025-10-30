from abc import abstractmethod
from typing import Protocol

from bot.exception import TicketPanelNotFound
from bot.database.models import TicketPanel, TicketType
from bot.database.schemas import TicketPanelSchema, TicketPanelCreate, TicketPanelUpdate

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import async_sessionmaker


class TicketPanelRepository(Protocol):
    """
    Abstract class for TicketPanelRepository
    Declares all methods available for TicketPanelRepository in the SQLAlchemy model or API
    """

    @abstractmethod
    async def get_all_ticket_panel(self) -> list[TicketPanelSchema]:
        """
        Get all ticket panels
        :return:
        """
        ...

    @abstractmethod
    async def get_all_ticket_panel_by_guild_id(self, guild_id: int) -> list[TicketPanelSchema]:
        """
        Get all ticket panels
        :param guild_id:
        :return:
        """
        ...

    @abstractmethod
    async def get_ticket_panel_by_id(self, ticket_panel_id: int,
                                     raise_if_not_found: bool = False) -> TicketPanelSchema | None:
        """
        Get ticket panel by id
        :param ticket_panel_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def get_ticket_panel_by_message_id(self, message_id: int,
                                             raise_if_not_found: bool = False) -> TicketPanelSchema | None:
        """
        Get ticket panel by message id
        :param message_id: Discord message ID
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def create_ticket_panel(self, ticket_panel: TicketPanelCreate) -> TicketPanelSchema:
        """
        Create a new ticket panel
        :param ticket_panel:
        :return:
        """
        ...

    @abstractmethod
    async def update_ticket_panel(self, ticket_panel: TicketPanelUpdate) -> TicketPanelSchema:
        """
        Update ticket panel
        :param ticket_panel:
        :return:
        """
        ...

    @abstractmethod
    async def delete_ticket_panel_by_id(self, ticket_panel_id: int) -> bool:
        """
        Delete ticket panel
        :param ticket_panel_id:
        :return:
        """
        ...

    @abstractmethod
    async def delete_ticket_panel(self, ticket_panel: TicketPanelSchema) -> bool:
        """
        Delete ticket panel
        :param ticket_panel:
        :return:
        """
        ...


class SQLAlchemyTicketPanelRepository(TicketPanelRepository):
    def __init__(self, session: async_sessionmaker):
        self.session = session

    async def get_all_ticket_panel(self) -> list[TicketPanelSchema]:
        async with self.session() as session:
            query = (
                select(TicketPanel)
                .options(selectinload(TicketPanel.ticket_type))
            )

            result = await session.execute(query)

            db_ticket_panels = result.scalars().all()

            return [TicketPanelSchema.model_validate(panel) for panel in db_ticket_panels]

    async def get_all_ticket_panel_by_guild_id(self, guild_id: int) -> list[TicketPanelSchema]:
        async with self.session() as session:
            query = (
                select(TicketPanel)
                .join(TicketPanel.ticket_type)
                .where(TicketType.guild_id == guild_id)
                .options(selectinload(TicketPanel.ticket_type))
            )

            result = await session.execute(query)

            db_ticket_panels = result.scalars().all()

            return [TicketPanelSchema.model_validate(panel) for panel in db_ticket_panels]

    async def get_ticket_panel_by_id(self, ticket_panel_id: int,
                                     raise_if_not_found: bool = False) -> TicketPanelSchema | None:
        async with self.session() as session:
            db_ticket_panel = await session.get(
                TicketPanel,
                ticket_panel_id,
                options=[selectinload(TicketPanel.ticket_type)],
            )

            if db_ticket_panel is None:
                if raise_if_not_found:
                    raise TicketPanelNotFound(ticket_panel_id)
                else:
                    return None

            return TicketPanelSchema.model_validate(db_ticket_panel)

    async def get_ticket_panel_by_message_id(self, message_id: int,
                                             raise_if_not_found: bool = False) -> TicketPanelSchema | None:
        async with self.session() as session:
            result = await session.execute(
                select(TicketPanel)
                .where(TicketPanel.message_id == message_id)
                .options(selectinload(TicketPanel.ticket_type))
            )

            db_ticket_panel = result.scalars().first()

            if db_ticket_panel is None:
                if raise_if_not_found:
                    raise TicketPanelNotFound(message_id)
                else:
                    return None

            return TicketPanelSchema.model_validate(db_ticket_panel)

    async def create_ticket_panel(self, ticket_panel: TicketPanelCreate) -> TicketPanelSchema:
        async with self.session() as session:
            db_ticket_panel = TicketPanel(**ticket_panel.model_dump())

            session.add(db_ticket_panel)
            await session.commit()
            await session.refresh(db_ticket_panel)

            return await self.get_ticket_panel_by_id(db_ticket_panel.id)

    async def update_ticket_panel(self, ticket_panel: TicketPanelUpdate) -> TicketPanelSchema:
        async with self.session() as session:
            db_ticket_panel = await session.get(
                TicketPanel,
                ticket_panel.id,
                options=[selectinload(TicketPanel.ticket_type)],
            )

            if db_ticket_panel is None:
                raise TicketPanelNotFound(ticket_panel)

            update_data = ticket_panel.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_ticket_panel, key, value)

            session.add(db_ticket_panel)
            await session.commit()
            await session.refresh(db_ticket_panel)

            return TicketPanelSchema.model_validate(db_ticket_panel)

    async def delete_ticket_panel_by_id(self, ticket_panel_id: int) -> bool:
        async with self.session() as session:
            db_ticket_panel = await session.get(TicketPanel, ticket_panel_id)

            if db_ticket_panel is None:
                return False

            await session.delete(db_ticket_panel)
            await session.commit()
            return True

    async def delete_ticket_panel(self, ticket_panel: TicketPanelSchema) -> bool:
        return await self.delete_ticket_panel_by_id(ticket_panel.id)
