from sqlalchemy import Integer, String, BigInteger, Float, DateTime, Enum, Boolean, ForeignKey, JSON, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from typing import Union, List
from datetime import datetime

from .schemas import InfractionType, InfractionResult, LogEntryType, ReportStatus, ReportAction, TicketStatus


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

    # Moderation
    report_channel_id: Mapped[Union[int, None]] = mapped_column(Integer, nullable=True, default=None)

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


class Report(Base):
    __tablename__ = "report"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False,
                                          index=True)

    reporter_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False)
    report_reason: Mapped[str] = mapped_column(String(512), nullable=False)
    offender_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False)

    reported_channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False)
    reported_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False)
    log_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False, unique=True)

    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), nullable=False, default=ReportStatus.OPEN)

    handler_id: Mapped[Union[int, None]] = mapped_column(BigInteger, nullable=True, autoincrement=False, default=None)
    handler_action: Mapped[Union[ReportAction, None]] = mapped_column(Enum(ReportAction), nullable=True, default=None)
    handled_at: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True, default=None)


class TicketType(Base):
    __tablename__ = "ticket_types"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False,
                                          index=True)

    name: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String(4096), nullable=False)

    ticket_channel_category_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False)

    requires_initial_reason: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    moderator_role_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False)

    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    deleted_at: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True, default=None)


class Tickets(Base):
    __tablename__ = "tickets"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ticket_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("ticket_types.id", ondelete="RESTRICT"),
                                                nullable=False)
    ticket_type: Mapped[TicketType] = relationship(TicketType)

    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), nullable=False, default=TicketStatus.OPEN)

    member_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False, index=True)
    channel_id: Mapped[Union[int, None]] = mapped_column(BigInteger, nullable=True, default=False, autoincrement=False,
                                                         index=True, unique=True)

    panel_message_id: Mapped[Union[int, None]] = mapped_column(BigInteger, nullable=True, default=None,
                                                               autoincrement=False, unique=True)

    handler_id: Mapped[Union[int, None]] = mapped_column(BigInteger, nullable=True, default=None)
    is_locked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    deleted_at: Mapped[Union[datetime, None]] = mapped_column(DateTime, nullable=True, default=None)


class TicketPanel(Base):
    __tablename__ = "ticket_panels"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    ticket_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("ticket_types.id", ondelete="RESTRICT"),
                                                nullable=False, index=True)
    ticket_type: Mapped[TicketType] = relationship(TicketType)

    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False, index=True)
    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False, unique=True, index=True)


class TicketMessage(Base):
    __tablename__ = "ticket_messages"
    __table_args__ = {'sqlite_autoincrement': True}

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[int] = mapped_column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)

    message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, autoincrement=False)
    author_id: Mapped[int] = mapped_column(BigInteger, nullable=False, autoincrement=False)

    content: Mapped[str] = mapped_column(Text, nullable=True)

    attachments_json: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    stickers_json: Mapped[list] = mapped_column(JSON, nullable=True, default=list)
    poll_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    reference_json: Mapped[dict] = mapped_column(JSON, nullable=True)
    embeds_json: Mapped[list] = mapped_column(JSON, nullable=True, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    edited_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=None)
    deleted_at: Mapped[datetime] = mapped_column(DateTime, nullable=True, default=None)
