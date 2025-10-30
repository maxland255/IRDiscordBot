from typing import Protocol
from abc import abstractmethod
from datetime import datetime, UTC

from bot.database.models import TicketMessage
from bot.exception import TicketMessageNotFound
from bot.database.schemas import TicketMessageSchema, TicketMessageCreate, TicketMessageUpdate

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker


class TicketMessageRepository(Protocol):
    """
    Define the TicketMessageRepository interface
    """

    @abstractmethod
    async def get_all_ticket_messages(self, ticket_id: int, include_deleted: bool = False) -> list[TicketMessageSchema]:
        """
        Get all ticket messages
        :param ticket_id:
        :param include_deleted:
        :return:
        """
        ...

    @abstractmethod
    async def get_ticket_message_by_id(self, ticket_message_id: int,
                                       raise_if_not_found: bool = False) -> TicketMessageSchema | None:
        """
        Get ticket message by id
        :param ticket_message_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def get_ticket_message_by_message_id(self, message_id: int,
                                               raise_if_not_found: bool = False) -> TicketMessageSchema | None:
        """
        Get ticket message by id
        :param message_id: Discord message id
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def create_ticket_message(self, ticket_message: TicketMessageCreate) -> TicketMessageSchema:
        """
        Create a new ticket message
        :param ticket_message:
        :return:
        """
        ...

    @abstractmethod
    async def update_ticket_message(self, ticket_message: TicketMessageUpdate) -> TicketMessageSchema:
        """
        Update new ticket message
        :param ticket_message:
        :return:
        """
        ...

    @abstractmethod
    async def delete_ticket_message_by_id(self, ticket_message_id: int) -> bool:
        """
        Delete a ticket message
        :param ticket_message_id:
        :return:
        """
        ...

    @abstractmethod
    async def delete_ticket_message_by_message_id(self, message_id: int) -> bool:
        """
        Delete a ticket message
        :param message_id: Discord message id
        :return:
        """
        ...

    @abstractmethod
    async def delete_ticket_message(self, ticket_message: TicketMessageSchema) -> bool:
        """
        Delete a ticket message
        :param ticket_message:
        :return:
        """
        ...

    @abstractmethod
    async def delete_multiple_ticket_messages(self, ticket_message_ids: list[int]) -> None:
        """
        Delete multiple ticket messages
        :param ticket_message_ids:
        :return:
        """
        ...


class SQLAlchemyTicketMessageRepository(TicketMessageRepository):
    def __init__(self, session: async_sessionmaker):
        self.session = session

    async def get_all_ticket_messages(self, ticket_id: int, include_deleted: bool = False) -> list[TicketMessageSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(TicketMessage)
                .where(
                    TicketMessage.ticket_id == ticket_id,
                    TicketMessage.deleted_at.is_(None) if not include_deleted else True
                )
            )

            db_ticket_messages = result.scalars().all()

            return [TicketMessageSchema.model_validate(ticket_message) for ticket_message in db_ticket_messages]

    async def get_ticket_message_by_id(self, ticket_message_id: int,
                                       raise_if_not_found: bool = False) -> TicketMessageSchema | None:
        async with self.session() as session:
            db_ticket_message = await session.get(TicketMessage, ticket_message_id)

            if db_ticket_message is None:
                if raise_if_not_found:
                    raise TicketMessageNotFound(ticket_message_id)
                else:
                    return None

            return TicketMessageSchema.model_validate(db_ticket_message)

    async def get_ticket_message_by_message_id(self, message_id: int,
                                               raise_if_not_found: bool = False) -> TicketMessageSchema | None:
        async with self.session() as session:
            result = await session.execute(
                select(TicketMessage)
                .where(TicketMessage.message_id == message_id)
            )

            db_ticket_message = result.scalars().first()

            if db_ticket_message is None:
                if raise_if_not_found:
                    raise TicketMessageNotFound(message_id)
                else:
                    return None

            return TicketMessageSchema.model_validate(db_ticket_message)

    async def create_ticket_message(self, ticket_message: TicketMessageCreate) -> TicketMessageSchema:
        async with self.session() as session:
            db_ticket_message = TicketMessage(**ticket_message.model_dump())

            session.add(db_ticket_message)
            await session.commit()
            await session.refresh(db_ticket_message)

            return TicketMessageSchema.model_validate(db_ticket_message)

    async def update_ticket_message(self, ticket_message: TicketMessageUpdate) -> TicketMessageSchema:
        async with self.session() as session:
            db_ticket_message = await session.get(TicketMessage, ticket_message.id)

            if db_ticket_message is None or db_ticket_message.deleted_at is not None:
                raise TicketMessageNotFound(ticket_message.id)

            update_data = ticket_message.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_ticket_message, key, value)

            session.add(db_ticket_message)
            await session.commit()
            await session.refresh(db_ticket_message)

            return TicketMessageSchema.model_validate(db_ticket_message)

    async def delete_ticket_message_by_id(self, ticket_message_id: int) -> bool:
        async with self.session() as session:
            db_ticket_message = await session.get(TicketMessage, ticket_message_id)

            if db_ticket_message is None or db_ticket_message.deleted_at is not None:
                return False

            db_ticket_message.deleted_at = datetime.now(UTC)
            session.add(db_ticket_message)
            await session.commit()

            return True

    async def delete_ticket_message_by_message_id(self, message_id: int) -> bool:
        async with self.session() as session:
            result = await session.execute(
                select(TicketMessage)
                .where(TicketMessage.message_id == message_id)
            )

            db_ticket_message = result.scalars().first()

            if db_ticket_message is None or db_ticket_message.deleted_at is not None:
                return False

            db_ticket_message.deleted_at = datetime.now(UTC)
            session.add(db_ticket_message)
            await session.commit()

            return True

    async def delete_ticket_message(self, ticket_message: TicketMessageSchema) -> bool:
        return await self.delete_ticket_message_by_id(ticket_message.id)

    async def delete_multiple_ticket_messages(self, ticket_message_ids: list[int]) -> None:
        async with self.session() as session:
            await session.execute(
                update(TicketMessage)
                .values(deleted_at=datetime.now(UTC))
                .where(TicketMessage.message_id.in_(ticket_message_ids))
            )
            await session.commit()
