from sqlalchemy import Integer, String, BigInteger, Float, DateTime, Enum, Boolean, ForeignKey, JSON
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from typing import Union, List
from datetime import datetime

from .schemas import InfractionType, InfractionResult, LogEntryType


class Base(DeclarativeBase):
    pass


class Guild(Base):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # Infractions
    warn_height: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)
    default_timeout: Mapped[int] = mapped_column(Integer, nullable=False, default=600)

    # salon de logs
    logs_moderation: Mapped[Union[int, None]] = mapped_column(Integer, default=None)
    logs_server: Mapped[Union[int, None]] = mapped_column(Integer, default=None)

    # Rules
    rules_channel_id: Mapped[Union[int, None]] = mapped_column(Integer, nullable=True, default=None)
    rules_message_id: Mapped[Union[List[int], None]] = mapped_column(JSON, nullable=True, default=None)

    # Tickets

    deleted_at: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True, default=None)


class GravityLevel(Base):
    __tablename__ = "gravity_levels"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False,
                                          index=True)

    name: Mapped[str] = mapped_column(String(25), nullable=False, unique=True)

    description: Mapped[str] = mapped_column(String(100), nullable=False)
    weight: Mapped[float] = mapped_column(Float, nullable=False)

    deleted_at: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True, default=None)


class Infractions(Base):
    __tablename__ = "infractions"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False,
                                          index=True)

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


class LogEntry(Base):
    __tablename__ = "logs"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False,
                                          index=True)

    log_type: Mapped[LogEntryType] = mapped_column(Enum(LogEntryType), nullable=False, index=True)

    actor_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False, index=True)
    target_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False, index=True)

    details: Mapped[dict] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now)


class GuildRules(Base):
    __tablename__ = "guild_rules"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False,
                                          index=True)

    title: Mapped[str] = mapped_column(String(256), nullable=False)
    rules: Mapped[str] = mapped_column(String(1024), nullable=False)

    rules_require_publish: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    deleted_at: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True, default=None)


class RoleOptions(Base):
    __tablename__ = "role_options"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    panel_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("role_panels.id", ondelete="CASCADE"), nullable=False,
                                          autoincrement=False, index=True)

    role_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False)

    emoji: Mapped[Union[str, None]] = mapped_column(String(10), nullable=True, default=None)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Union[str, None]] = mapped_column(String(100), nullable=True, default=None)

    panel: Mapped["RolePanel"] = relationship("RolePanel", back_populates="options")


class RolePanel(Base):
    __tablename__ = "role_panels"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False,
                                          index=True)

    channel_id: Mapped[Union[int, None]] = mapped_column(BigInteger, nullable=True, autoincrement=False)
    message_id: Mapped[Union[int, None]] = mapped_column(BigInteger, nullable=True, autoincrement=False)

    multiple_choose: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # An internal name to identify the panel
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # A title and description to display above the options
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[Union[str, None]] = mapped_column(String(4096), nullable=True, default=None)

    deleted_at: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True, default=None)

    options: Mapped[List[RoleOptions]] = relationship(RoleOptions, back_populates="panel")
