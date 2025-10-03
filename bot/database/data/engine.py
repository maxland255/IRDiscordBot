from ..core.config import get_settings

from sqlalchemy import Integer, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

_settings = get_settings()

engine = create_async_engine(_settings.DATABASE_URL, echo=_settings.DEV)

AsyncSession = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, email={self.email})>"


async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession() as session:
        user1 = User(name="Alice", email="alice@example.com")
        user2 = User(name="Bob", email="bob@example.com")

        session.add_all([user1, user2])

        await session.commit()

    async with AsyncSession() as session:
        query = select(User)

        result = await session.execute(query)

        all_users = result.scalars().all()

        for user in all_users:
            print(user)
