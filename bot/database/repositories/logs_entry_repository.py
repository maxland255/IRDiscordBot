from abc import abstractmethod

from typing import Protocol

from bot.database.schemas import LogEntryCreate, LogEntrySchema
from bot.database.models import LogEntry

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker


class LogsEntryRepository(Protocol):
    """
    Declare all methode available in the Logs Entry Repository.
    This is the unique API for all data sources.
    """

    @abstractmethod
    async def get_all_logs_by_guild_id(self, guild_id: int) -> list[LogEntrySchema]:
        """
        Get all Log Entry data for a specific guild.
        :param guild_id:
        :return:
        """
        ...

    @abstractmethod
    async def create_log_entry(self, log_entry: LogEntryCreate) -> LogEntrySchema:
        """
        Create Log Entry data.
        :param log_entry:
        :return:
        """
        ...


class SQLAlchemyLogsEntryRepository(LogsEntryRepository):
    def __init__(self, session: async_sessionmaker):
        self.session = session

    async def get_all_logs_by_guild_id(self, guild_id: int) -> list[LogEntrySchema]:
        async with self.session() as session:
            result = await session.execute(
                select(LogEntry)
                .where(LogEntry.guild_id == guild_id)
            )

            all_logs_entries = result.all()

            return [LogEntrySchema.model_validate(log_entry) for log_entry in all_logs_entries]

    async def create_log_entry(self, log_entry: LogEntryCreate) -> LogEntrySchema:
        async with self.session() as session:
            db_log_entry = LogEntry(**log_entry.model_dump())

            session.add(db_log_entry)
            await session.commit()
            await session.refresh(db_log_entry)

            return LogEntrySchema.model_validate(db_log_entry)
