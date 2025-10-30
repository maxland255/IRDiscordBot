from typing import Protocol
from abc import abstractmethod
from datetime import datetime, UTC

from bot.database.models import TicketType
from bot.exception import TicketTypeNotFound
from bot.database.schemas import TicketTypeCreate, TicketTypeSchema, TicketTypeUpdate

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker


class TicketTypeRepository(Protocol):
    """
    Declare all methode available in the Ticket Type Repository.
    This is the unique API for all data sources.
    """

    @abstractmethod
    async def get_all_ticket_types(self, guild_id: int) -> list[TicketTypeSchema]:
        """
        Get all ticket types.
        :param guild_id:
        :return:
        """
        ...

    @abstractmethod
    async def get_ticket_type_by_id(self, ticket_type_id: int,
                                    raise_if_not_found: bool = False) -> TicketTypeSchema | None:
        """
        Get ticket type by id.
        :param ticket_type_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def create_ticket_type(self, ticket_type: TicketTypeCreate) -> TicketTypeSchema:
        """
        Create a new ticket type.
        :param ticket_type:
        :return:
        """
        ...

    @abstractmethod
    async def update_ticket_type(self, ticket_type: TicketTypeUpdate) -> TicketTypeSchema:
        """
        Update a ticket type.
        :param ticket_type:
        :return:
        """
        ...

    @abstractmethod
    async def delete_ticket_type(self, ticket_type: TicketTypeSchema) -> bool:
        """
        Delete a ticket type.
        :param ticket_type:
        :return:
        """
        ...


class SQLAlchemyTicketTypeRepository(TicketTypeRepository):
    def __init__(self, session: async_sessionmaker):
        self.session = session

    async def get_all_ticket_types(self, guild_id: int) -> list[TicketTypeSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(TicketType)
                .where(
                    TicketType.guild_id == guild_id,
                    TicketType.deleted_at.is_(None),
                )
            )

            db_ticket_type = result.scalars().all()

            return [TicketTypeSchema.model_validate(t) for t in db_ticket_type]

    async def get_ticket_type_by_id(self, ticket_type_id: int,
                                    raise_if_not_found: bool = False) -> TicketTypeSchema | None:
        async with self.session() as session:
            db_ticket_type = await session.get(TicketType, ticket_type_id)

            if db_ticket_type is None:
                if raise_if_not_found:
                    raise TicketTypeNotFound(ticket_type_id)
                else:
                    return None

            return TicketTypeSchema.model_validate(db_ticket_type)

    async def create_ticket_type(self, ticket_type: TicketTypeCreate) -> TicketTypeSchema:
        async with self.session() as session:
            db_ticket_type = TicketType(**ticket_type.model_dump())

            session.add(db_ticket_type)
            await session.commit()
            await session.refresh(db_ticket_type)

            return TicketTypeSchema.model_validate(db_ticket_type)

    async def update_ticket_type(self, ticket_type: TicketTypeUpdate) -> TicketTypeSchema:
        async with self.session() as session:
            db_ticket_type = await session.get(TicketType, ticket_type.id)

            if db_ticket_type is None or db_ticket_type.deleted_at is not None:
                raise TicketTypeNotFound(ticket_type)

            update_data = ticket_type.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_ticket_type, key, value)

            session.add(db_ticket_type)
            await session.commit()
            await session.refresh(db_ticket_type)

            return TicketTypeSchema.model_validate(db_ticket_type)

    async def delete_ticket_type(self, ticket_type: TicketTypeSchema) -> bool:
        async with self.session() as session:
            db_ticket_type = await session.get(TicketType, ticket_type.id)

            if db_ticket_type is None or db_ticket_type.deleted_at is not None:
                raise False

            db_ticket_type.deleted_at = datetime.now(UTC)

            session.add(db_ticket_type)
            await session.commit()

            return True
