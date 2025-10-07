from sqlalchemy import Integer, String, BigInteger, Float, DateTime, Enum, Boolean, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from typing import Union
from datetime import datetime

from .schemas import InfractionType, InfractionResult


class Base(DeclarativeBase):
    pass


class Guild(Base):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    warn_height: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)

    default_timeout: Mapped[int] = mapped_column(Integer, nullable=False, default=600)

    # salon de logs
    logs_moderation: Mapped[Union[int, None]] = mapped_column(Integer, default=None)
    logs_server: Mapped[Union[int, None]] = mapped_column(Integer, default=None)

    deleted_at: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True, default=None)


class GravityLevel(Base):
    __tablename__ = "gravity_levels"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)

    name: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)

    description: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)

    deleted_at: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True, default=None)


class Infractions(Base):
    __tablename__ = "infractions"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False)
    moderator_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False)

    reason: Mapped[str] = mapped_column(String(255), nullable=False)

    infraction_type: Mapped[InfractionType] = mapped_column(Enum(InfractionType), nullable=False)

    gravity_id: Mapped[Union[int, None]] = mapped_column(BigInteger,
                                                         ForeignKey("gravity_levels.id", ondelete="RESTRICT"),
                                                         nullable=True)
    gravity: Mapped[Union[GravityLevel, None]] = relationship(GravityLevel)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now)

    infraction_result: Mapped[InfractionResult] = mapped_column(Enum(InfractionResult), nullable=False)
    timeout_end: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    deleted_at: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True, default=None)
