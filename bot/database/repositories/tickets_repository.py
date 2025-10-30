import logging

from typing import Protocol
from abc import abstractmethod
from datetime import datetime, UTC

from bot.exception import TicketsNotFound
from bot.database.models import Tickets, TicketType
from bot.database.schemas import TicketsSchema, TicketsCreate, TicketsUpdate, TicketStatus

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import async_sessionmaker

logger = logging.getLogger(__name__)


class TicketsRepository(Protocol):
    """
    Define the TicketsRepository interface
    It's used to define the TicketsRepository interface for SQLAlchemy and API
    """

    @abstractmethod
    async def get_all_open_tickets(self) -> list[TicketsSchema]:
        """
        Get all open tickets
        :return:
        """
        ...

    @abstractmethod
    async def get_all_tickets_by_guild_id(self, guild_id: int, status: TicketStatus | None = None) -> list[
        TicketsSchema]:
        """
        Get all tickets for a guild
        :param guild_id:
        :param status:
        :return:
        """
        ...

    @abstractmethod
    async def get_ticket_by_id(self, ticket_id: int, raise_if_not_found: bool = False) -> TicketsSchema | None:
        """
        Get ticket by id
        :param ticket_id::
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def get_ticket_by_channel_id(self, channel_id: int, raise_if_not_found: bool = False) -> TicketsSchema | None:
        """
        Get ticket by channel id
        :param channel_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def get_all_tickets_by_member_id(self, member_id: int) -> list[TicketsSchema]:
        """
        Get all tickets for a member
        :param member_id:
        :return:
        """
        ...

    @abstractmethod
    async def create_ticket(self, ticket: TicketsCreate) -> TicketsSchema:
        """
        Create a new ticket
        :param ticket:
        :return:
        """
        ...

    @abstractmethod
    async def update_ticket(self, ticket: TicketsUpdate) -> TicketsSchema:
        """
        Update a ticket
        :param ticket:
        :return:
        """
        ...

    @abstractmethod
    async def delete_ticket_by_id(self, ticket_id: int) -> bool:
        """
        Delete a ticket
        :param ticket_id:
        :return:
        """
        ...

    @abstractmethod
    async def delete_ticket(self, ticket: TicketsSchema) -> bool:
        """
        Delete a ticket
        :param ticket:
        :return:
        """
        ...

    @abstractmethod
    async def find_open_ticket_by_member_id_guild_id_and_type_id(self, guild_id: int, member_id: int,
                                                                 type_id: int) -> bool:
        """
        Find open tickets by member id, guild id and type id
        :param guild_id:
        :param member_id:
        :param type_id:
        :return:
        """
        ...


class SQLAlchemyTicketsRepository(TicketsRepository):
    def __init__(self, session: async_sessionmaker):
        self.session = session

    async def get_all_open_tickets(self) -> list[TicketsSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(Tickets)
                .where(Tickets.status == TicketStatus.OPEN)
                .options(selectinload(Tickets.ticket_type))
            )

            db_tickets = result.scalars().all()

            return [TicketsSchema.model_validate(ticket) for ticket in db_tickets]

    async def get_all_tickets_by_guild_id(self, guild_id: int, status: TicketStatus | None = None) -> list[
        TicketsSchema]:
        if status is not None:
            logger.error("The parameters 'status' is not implemented for the moment")

        async with self.session() as session:
            query = (
                select(Tickets)
                .join(Tickets.ticket_type)
                .where(
                    TicketType.guild_id == guild_id,
                    Tickets.deleted_at.is_(None)
                )
                .options(selectinload(Tickets.ticket_type))
            )

            result = await session.execute(query)

            db_tickets = result.scalars().all()

            return [TicketsSchema.model_validate(ticket) for ticket in db_tickets]

    async def get_ticket_by_id(self, ticket_id: int, raise_if_not_found: bool = False) -> TicketsSchema | None:
        async with self.session() as session:
            db_ticket = await session.get(Tickets, ticket_id, options=[selectinload(Tickets.ticket_type)])

            if db_ticket is None:
                if raise_if_not_found:
                    raise TicketsNotFound(ticket_id)
                else:
                    return None

            return TicketsSchema.model_validate(db_ticket)

    async def get_ticket_by_channel_id(self, channel_id: int, raise_if_not_found: bool = False) -> TicketsSchema | None:
        async with self.session() as session:
            result = await session.execute(
                select(Tickets)
                .where(Tickets.channel_id == channel_id)
                .options(selectinload(Tickets.ticket_type))
            )

            db_ticket = result.scalars().first()

            if db_ticket is None:
                if raise_if_not_found:
                    raise TicketsNotFound(channel_id)
                else:
                    return None

            return TicketsSchema.model_validate(db_ticket)

    async def get_all_tickets_by_member_id(self, member_id: int) -> list[TicketsSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(Tickets)
                .where(Tickets.member_id == member_id)
                .options(selectinload(Tickets.ticket_type))
            )

            db_tickets = result.scalars().all()

            return [TicketsSchema.model_validate(ticket) for ticket in db_tickets]

    async def create_ticket(self, ticket: TicketsCreate) -> TicketsSchema:
        async with self.session() as session:
            db_ticket = Tickets(**ticket.model_dump())

            session.add(db_ticket)
            await session.commit()
            await session.refresh(db_ticket)

            return await self.get_ticket_by_id(db_ticket.id)

    async def update_ticket(self, ticket: TicketsUpdate) -> TicketsSchema:
        async with self.session() as session:
            db_ticket = await session.get(Tickets, ticket.id, options=[selectinload(Tickets.ticket_type)])

            if db_ticket is None or db_ticket.deleted_at is not None:
                raise TicketsNotFound(ticket)

            update_data = ticket.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_ticket, key, value)

            session.add(db_ticket)
            await session.commit()
            await session.refresh(db_ticket)

            return TicketsSchema.model_validate(db_ticket)

    async def delete_ticket_by_id(self, ticket_id: int) -> bool:
        async with self.session() as session:
            db_ticket = await session.get(Tickets, ticket_id)

            if db_ticket is None or db_ticket.deleted_at is not None:
                return False

            db_ticket.deleted_at = datetime.now(UTC)
            session.add(db_ticket)
            await session.commit()
            return True

    async def delete_ticket(self, ticket: TicketsSchema) -> bool:
        return await self.delete_ticket_by_id(ticket.id)

    async def find_open_ticket_by_member_id_guild_id_and_type_id(self, guild_id: int, member_id: int,
                                                                 type_id: int) -> bool:
        async with self.session() as session:
            result = await session.execute(
                select(Tickets)
                .join(Tickets.ticket_type)
                .where(
                    TicketType.guild_id == guild_id,
                    Tickets.member_id == member_id,
                    Tickets.ticket_type_id == type_id,
                    Tickets.status == TicketStatus.OPEN,
                    Tickets.deleted_at.is_(None)
                )
                .options(selectinload(Tickets.ticket_type))
            )

            db_tickets = result.scalar_one_or_none()

            return db_tickets is not None
