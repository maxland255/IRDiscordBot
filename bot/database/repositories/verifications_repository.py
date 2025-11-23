from typing import Protocol
from abc import abstractmethod
from datetime import datetime, UTC, timedelta

from bot.database.models import Verifications
from bot.exception import VerificationNotFound, VerificationRateLimitError
from bot.database.schemas import VerificationStatus, VerificationsSchema, VerificationsCreate, VerificationsUpdate

from sqlalchemy import select, update, or_
from sqlalchemy.ext.asyncio import async_sessionmaker


class VerificationsRepository(Protocol):
    """
    Define the VerificationsRepository interface
    It's used to define the VerificationsRepository interface for SQLAlchemy and API
    """

    @abstractmethod
    async def get_all_verifications_by_guild_id(self, guild_id: int, status: VerificationStatus) -> list[
        VerificationsSchema]:
        """
        Get all verifications for a guild
        :param guild_id:
        :param status:
        :return:
        """
        ...

    @abstractmethod
    async def get_all_verifications_by_status(self, guild_id: int, status: list[VerificationStatus]) -> list[
        VerificationsSchema]:
        """
        Get all verifications for a guild by multiple status
        :param guild_id:
        :param status:
        :return:
        """
        ...

    @abstractmethod
    async def get_verification_by_id(self, verification_id: int,
                                     raise_if_not_found: bool = False) -> VerificationsSchema | None:
        """
        Get verification
        :param verification_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def get_verification_by_user_id(self, guild_id: int, user_id: int,
                                          raise_if_not_found: bool = False) -> VerificationsSchema | None:
        """
        Get verification for a specific member
        :param guild_id:
        :param user_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def get_unverified_members_past_date(self, guild_id: int, past_date: datetime) -> list[VerificationsSchema]:
        """
        Get unverified members past a specific date
        :param guild_id:
        :param past_date:
        :return:
        """
        ...

    @abstractmethod
    async def get_expired_students(self, now: datetime) -> list[VerificationsSchema]:
        """
        Get expired students
        :param now:
        :return:
        """
        ...

    @abstractmethod
    async def get_reverification_reminders(self, reminder_threshold_date: datetime) -> list[VerificationsSchema]:
        """
        Get verifications that need reverification reminders sent
        :param reminder_threshold_date:
        :return:
        """
        ...

    @abstractmethod
    async def get_expired_grace_periods(self, now: datetime) -> list[VerificationsSchema]:
        """
        Get verifications with expired grace periods
        :param now:
        :return:
        """
        ...

    @abstractmethod
    async def create_verification(self, verification: VerificationsCreate) -> VerificationsSchema:
        """
        Create verification
        :param verification:
        :return:
        """
        ...

    @abstractmethod
    async def update_verification(self, verification: VerificationsUpdate) -> VerificationsSchema:
        """
        Update a verification data
        :param verification:
        :return:
        """
        ...

    @abstractmethod
    async def start_reverification(self, verification_id: int, grace_period_end_date: datetime) -> None:
        """
        Start reverification for specific verification
        :param verification_id:
        :param grace_period_end_date:
        :return:
        """
        ...

    @abstractmethod
    async def mark_reminder_sent(self, verification_id: int, sent_at: datetime) -> None:
        """
        Mark a reverification reminder as sent
        :param verification_id:
        :param sent_at:
        :return:
        """
        ...

    @abstractmethod
    async def delete_verification_by_id(self, verification_id: int) -> bool:
        """
        Delete verification for a specific id
        :param verification_id:
        :return:
        """
        ...

    @abstractmethod
    async def delete_verification_by_user_id(self, guild_id: int, user_id: int) -> bool:
        """
        Delete verification for a user id on a specific guild id
        :param guild_id:
        :param user_id:
        :return:
        """
        ...

    @abstractmethod
    async def delete_verification(self, verification: VerificationsSchema) -> bool:
        """
        Delete a verification
        :param verification:
        :return:
        """
        ...

    @abstractmethod
    async def check_email_rate_limit(self, guild_id: int, user_id: int) -> None:
        """
        Check if a user has reached the email rate limit
        :param guild_id:
        :param user_id:
        :return:
        """
        ...


class SQLAlchemyVerificationsRepository(VerificationsRepository):
    def __init__(self, session: async_sessionmaker):
        self.session = session

    async def get_all_verifications_by_guild_id(self, guild_id: int, status: VerificationStatus) -> list[
        VerificationsSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(Verifications)
                .where(
                    Verifications.guild_id == guild_id,
                    Verifications.status == status,
                )
            )

            db_verifications = result.scalars().all()

            return [VerificationsSchema.model_validate(verification) for verification in db_verifications]

    async def get_all_verifications_by_status(self, guild_id: int, status: list[VerificationStatus]) -> list[
        VerificationsSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(Verifications)
                .where(
                    Verifications.guild_id == guild_id,
                    or_(Verifications.status == s for s in status),
                )
            )

            db_verifications = result.scalars().all()

            return [VerificationsSchema.model_validate(verification) for verification in db_verifications]

    async def get_verification_by_id(self, verification_id: int,
                                     raise_if_not_found: bool = False) -> VerificationsSchema | None:
        async with self.session() as session:
            db_verification = await session.get(Verifications, verification_id)

            if db_verification is None:
                if raise_if_not_found:
                    raise VerificationNotFound(verification_id)
                else:
                    return None

            return VerificationsSchema.model_validate(db_verification)

    async def get_verification_by_user_id(self, guild_id: int, user_id: int,
                                          raise_if_not_found: bool = False) -> VerificationsSchema | None:
        async with self.session() as session:
            result = await session.execute(
                select(Verifications)
                .where(
                    Verifications.guild_id == guild_id,
                    Verifications.user_id == user_id,
                )
            )

            db_verification = result.scalars().first()

            if db_verification is None:
                if raise_if_not_found:
                    raise VerificationNotFound(f"{guild_id}-{user_id}")
                else:
                    return None

            return VerificationsSchema.model_validate(db_verification)

    async def get_unverified_members_past_date(self, guild_id: int, past_date: datetime) -> list[VerificationsSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(Verifications)
                .where(
                    Verifications.guild_id == guild_id,
                    Verifications.status == VerificationStatus.pending_email,
                    Verifications.joined_at <= past_date,
                )
            )

            db_verifications = result.scalars().all()

            return [VerificationsSchema.model_validate(verification) for verification in db_verifications]

    async def get_expired_students(self, now: datetime) -> list[VerificationsSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(Verifications)
                .where(
                    Verifications.status == VerificationStatus.verified_student,
                    Verifications.verification_expires_at < now,
                )
            )

            db_verifications = result.scalars().all()

            return [VerificationsSchema.model_validate(verification) for verification in db_verifications]

    async def get_reverification_reminders(self, reminder_threshold_date: datetime) -> list[VerificationsSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(Verifications)
                .where(
                    Verifications.status == VerificationStatus.pending_reverification,
                    Verifications.grace_period_ends_at < reminder_threshold_date,
                    Verifications.last_reminder_sent_at.is_(None),
                )
            )

            db_verifications = result.scalars().all()

            return [VerificationsSchema.model_validate(verification) for verification in db_verifications]

    async def get_expired_grace_periods(self, now: datetime) -> list[VerificationsSchema]:
        async with self.session() as session:
            result = await session.execute(
                select(Verifications)
                .where(
                    Verifications.status == VerificationStatus.pending_reverification,
                    Verifications.grace_period_ends_at < now,
                )
            )

            db_verifications = result.scalars().all()

            return [VerificationsSchema.model_validate(verification) for verification in db_verifications]

    async def create_verification(self, verification: VerificationsCreate) -> VerificationsSchema:
        async with self.session() as session:
            db_verification = Verifications(**verification.model_dump())

            session.add(db_verification)
            await session.commit()
            await session.refresh(db_verification)

            return VerificationsSchema.model_validate(db_verification)

    async def update_verification(self, verification: VerificationsUpdate) -> VerificationsSchema:
        async with self.session() as session:
            db_verification = await session.get(Verifications, verification.id)

            if db_verification is None:
                raise VerificationNotFound(verification)

            update_data = verification.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_verification, key, value)

            session.add(db_verification)
            await session.commit()
            await session.refresh(db_verification)

            return VerificationsSchema.model_validate(db_verification)

    async def start_reverification(self, verification_id: int, grace_period_end_date: datetime) -> None:
        async with self.session() as session:
            stmt = (
                update(Verifications)
                .where(Verifications.id == verification_id)
                .values(
                    status=VerificationStatus.pending_reverification,
                    grace_period_ends_at=grace_period_end_date,
                    last_reminder_sent_at=None,
                )
            )

            await session.execute(stmt)
            await session.commit()

    async def mark_reminder_sent(self, verification_id: int, sent_at: datetime) -> None:
        async with self.session() as session:
            stmt = (
                update(Verifications)
                .where(Verifications.id == verification_id)
                .values(last_reminder_sent_at=sent_at)
            )
            await session.execute(stmt)
            await session.commit()

    async def delete_verification_by_id(self, verification_id: int) -> bool:
        async with self.session() as session:
            db_verification = await session.get(Verifications, verification_id)

            if db_verification is None:
                return False

            db_verification.deleted_at = datetime.now(UTC)
            session.add(db_verification)
            await session.commit()

            return True

    # TODO: Test the implementation
    async def delete_verification_by_user_id(self, guild_id: int, user_id: int) -> bool:
        async with self.session() as session:
            result = await session.execute(
                update(Verifications)
                .values(deleted_at=datetime.now(UTC))
                .where(
                    Verifications.guild_id == guild_id,
                    Verifications.user_id == user_id,
                )
            )

            await session.commit()

            return result.scalar_one_or_none() is not None

    async def delete_verification(self, verification: VerificationsSchema) -> bool:
        return await self.delete_verification_by_id(verification.id)

    async def check_email_rate_limit(self, guild_id: int, user_id: int) -> None:
        async with self.session() as session:
            entry = await self.get_verification_by_user_id(guild_id, user_id, raise_if_not_found=True)

            now = datetime.now(UTC)
            today = now.date()

            update_verification = VerificationsUpdate(
                id=entry.id,
            )

            if entry.last_email_sent_at:
                last_email_sent_at = entry.last_email_sent_at.replace(tzinfo=UTC)

                cooldown_end = last_email_sent_at + timedelta(minutes=2)
                if now < cooldown_end:
                    retry_after = (cooldown_end - now).total_seconds()
                    raise VerificationRateLimitError("Email send rate limit exceeded. Please wait before trying again.",
                                                     retry_after)

            if entry.last_attempt_date != today:
                update_verification.daily_attempts = 0
                update_verification.last_attempt_date = today

            if entry.daily_attempts >= 5:
                tomorrow = now.date() + timedelta(days=1)

                raise VerificationRateLimitError(
                    "You have reached the maximum number of email verification attempts for today. Please try again tomorrow.",
                    retry_after=(datetime.combine(tomorrow, datetime.min.time(), tzinfo=UTC) - now).total_seconds()
                )

            if update_verification.daily_attempts is None:
                update_verification.daily_attempts = 0

            update_verification.daily_attempts += 1
            update_verification.last_email_sent_at = now

            await self.update_verification(update_verification)
