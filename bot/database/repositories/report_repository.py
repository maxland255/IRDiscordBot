from abc import abstractmethod
from typing import Protocol

from bot.database.models import Report
from bot.exception import ReportNotFound
from bot.database.schemas import ReportSchema, ReportCreate, ReportUpdate

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker


class ReportRepository(Protocol):
    """
    Declare all methode available in the Report Repository.
    This is the unique API for all data sources.
    """

    @abstractmethod
    async def get_report_by_id(self, report_id: int, raise_if_not_found: bool = False) -> ReportSchema | None:
        """
        Get a report by its id.
        :param report_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def get_report_by_log_message_id(self, log_message_id: int,
                                           raise_if_not_found: bool = False) -> ReportSchema | None:
        """
        Get a report by its log message id.
        :param log_message_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def create_report(self, report: ReportCreate) -> ReportSchema:
        """
        Create a report.
        :param report:
        :return:
        """
        ...

    @abstractmethod
    async def update_report(self, report: ReportUpdate) -> ReportSchema:
        """
        Update a report.
        :param report:
        :return:
        """
        ...


class SQLAlchemyReportRepository(ReportRepository):
    def __init__(self, session: async_sessionmaker):
        self.session = session

    async def get_report_by_id(self, report_id: int, raise_if_not_found: bool = False) -> ReportSchema | None:
        async with self.session() as session:
            db_report = await session.get(Report, report_id)

            if db_report is None:
                if raise_if_not_found:
                    raise ReportNotFound(report_id)
                else:
                    return None

            return ReportSchema.model_validate(db_report)

    async def get_report_by_log_message_id(self, log_message_id: int,
                                           raise_if_not_found: bool = False) -> ReportSchema | None:
        async with self.session() as session:
            db_report = await session.execute(
                select(Report)
                .where(Report.log_message_id == log_message_id)
            )

            db_report = db_report.scalars().first()

            if db_report is None:
                if raise_if_not_found:
                    raise ReportNotFound(log_message_id)
                else:
                    return None

            return ReportSchema.model_validate(db_report)

    async def create_report(self, report: ReportCreate) -> ReportSchema:
        async with self.session() as session:
            db_report = Report(**report.model_dump())

            session.add(db_report)
            await session.commit()
            await session.refresh(db_report)

            return ReportSchema.model_validate(db_report)

    async def update_report(self, report: ReportUpdate) -> ReportSchema:
        async with self.session() as session:
            db_report = await session.get(Report, report.id)

            if db_report is None:
                raise ReportNotFound(report.id)

            update_data = report.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_report, key, value)

            session.add(db_report)
            await session.commit()
            await session.refresh(db_report)

            return ReportSchema.model_validate(db_report)
