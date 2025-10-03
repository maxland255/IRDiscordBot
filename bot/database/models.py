from sqlalchemy import Integer, String, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Guild(Base):
    __tablename__ = "guilds"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)

    # salon de logs
    logs_moderation: Mapped[int] = mapped_column(Integer, default=None)
    logs_server: Mapped[int] = mapped_column(Integer, default=None)
