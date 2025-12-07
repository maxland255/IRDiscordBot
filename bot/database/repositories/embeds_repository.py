from abc import abstractmethod
from typing import Protocol
from datetime import datetime, UTC

from bot.database.models import Embeds, EmbedFields
from bot.database.schemas import EmbedsCreate, EmbedsSchema, EmbedsUpdate, EmbedFieldsCreate, EmbedFieldsSchema, \
    EmbedFieldsUpdate
from bot.exception import EmbedsNotFound, EmbedFieldsNotFound

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import async_sessionmaker


class EmbedsRepository(Protocol):
    """
    Declare all methode available in the Embeds Repository.
    This is the unique API for all data sources.
    """

    @abstractmethod
    async def get_all_embeds(self, guild_id: int) -> list[EmbedsSchema]:
        """
        Get all Embeds data.
        :return:
        """
        ...

    @abstractmethod
    async def get_specific_embed(self, embed_id: int, raise_if_not_found: bool = False) -> EmbedsSchema | None:
        """
        Get specific Embeds data.
        :param embed_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def create_embeds(self, embed: EmbedsCreate) -> EmbedsSchema:
        """
        Create Embeds data.
        :param embed:
        :return:
        """
        ...

    @abstractmethod
    async def update_embeds(self, embed: EmbedsUpdate) -> EmbedsSchema:
        """
        Update Embeds data.
        :param embed:
        :return:
        """
        ...

    @abstractmethod
    async def delete_embeds_by_id(self, embed_id: int) -> None:
        """
        Soft delete specific Embeds data by ID.
        :param embed_id:
        :return:
        """
        ...

    @abstractmethod
    async def delete_embeds(self, embed: EmbedsSchema) -> None:
        """
        Soft delete specific Embeds data.
        :param embed:
        :return:
        """
        ...

    @abstractmethod
    async def get_all_embed_fields(self, embed_id: int) -> list[EmbedFieldsSchema]:
        """
        Get all Embed Fields data for a specific embed.
        :param embed_id:
        :return:
        """
        ...

    @abstractmethod
    async def get_specific_embed_field(self, embed_field_id: int,
                                       raise_if_not_found: bool = False) -> EmbedFieldsSchema | None:
        """
        Get specific Embed Field data.
        :param embed_field_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def create_embed_fields(self, embed: EmbedFieldsCreate) -> EmbedFieldsSchema:
        """
        Create Embed Fields data.
        :param embed:
        :return:
        """
        ...

    @abstractmethod
    async def update_embed_fields(self, embed_field: EmbedFieldsUpdate) -> EmbedFieldsSchema:
        """
        Update Embed Fields data.
        :param embed_field:
        :return:
        """
        ...

    @abstractmethod
    async def delete_embed_fields_by_id(self, embed_field_id: int) -> None:
        """
        Soft delete specific Embed Fields data by ID.
        :param embed_field_id:
        :return:
        """
        ...

    @abstractmethod
    async def delete_embed_fields(self, embed_field: EmbedFieldsSchema) -> None:
        """
        Soft delete specific Embed Fields data.
        :param embed_field:
        :return:
        """
        ...

    @abstractmethod
    async def get_next_position(self, embed_id: int) -> int:
        """
        Get the next position for an embed field in a specific embed.
        :param embed_id:
        :return:
        """
        ...


class SQLAlchemyEmbedsRepository(EmbedsRepository):
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def get_all_embeds(self, guild_id: int) -> list[EmbedsSchema]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(Embeds)
                .where(
                    Embeds.guild_id == guild_id,
                    Embeds.deleted_at.is_(None),
                )
            )

            db_embeds = result.scalars().all()

            return [EmbedsSchema.model_validate(embed) for embed in db_embeds]

    async def get_specific_embed(self, embed_id: int, raise_if_not_found: bool = False) -> EmbedsSchema | None:
        async with self.session_factory() as session:
            db_embed = await session.get(Embeds, embed_id)

            if db_embed is None or db_embed.deleted_at is not None:
                if raise_if_not_found:
                    raise EmbedsNotFound(embed_id)
                else:
                    return None

            return EmbedsSchema.model_validate(db_embed)

    async def create_embeds(self, embed: EmbedsCreate) -> EmbedsSchema:
        async with self.session_factory() as session:
            db_embed = Embeds(**embed.model_dump())

            session.add(db_embed)
            await session.commit()
            await session.refresh(db_embed)

            return EmbedsSchema.model_validate(db_embed)

    async def update_embeds(self, embed: EmbedsUpdate) -> EmbedsSchema:
        async with self.session_factory() as session:
            db_embed = await session.get(Embeds, embed.id)

            if db_embed is None:
                raise EmbedsNotFound(embed.id)

            update_data = embed.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(db_embed, field, value)

            session.add(db_embed)
            await session.commit()
            await session.refresh(db_embed)

            return EmbedsSchema.model_validate(db_embed)

    async def delete_embeds_by_id(self, embed_id: int) -> None:
        async with self.session_factory() as session:
            db_embed = await session.get(Embeds, embed_id)

            if db_embed is None or db_embed.deleted_at is not None:
                raise EmbedsNotFound(embed_id)

            db_embed.deleted_at = datetime.now(UTC)

            session.add(db_embed)
            await session.commit()

    async def delete_embeds(self, embed: EmbedsSchema) -> None:
        await self.delete_embeds_by_id(embed.id)

    async def get_all_embed_fields(self, embed_id: int) -> list[EmbedFieldsSchema]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(EmbedFields)
                .where(
                    EmbedFields.embed_id == embed_id,
                    EmbedFields.deleted_at.is_(None),
                )
                .order_by(EmbedFields.position)
                .options(selectinload(EmbedFields.embed))
            )

            db_embed_fields = result.scalars().all()

            return [EmbedFieldsSchema.model_validate(embed_field) for embed_field in db_embed_fields]

    async def get_specific_embed_field(self, embed_field_id: int,
                                       raise_if_not_found: bool = False) -> EmbedFieldsSchema | None:
        async with self.session_factory() as session:
            db_embed_field = await session.get(EmbedFields, embed_field_id, options=[selectinload(EmbedFields.embed)])

            if db_embed_field is None or db_embed_field.deleted_at is not None:
                if raise_if_not_found:
                    raise EmbedFieldsNotFound(embed_field_id)
                else:
                    return None

            return EmbedFieldsSchema.model_validate(db_embed_field)

    async def create_embed_fields(self, embed: EmbedFieldsCreate) -> EmbedFieldsSchema:
        async with self.session_factory() as session:
            db_embed_field = EmbedFields(**embed.model_dump())

            session.add(db_embed_field)
            await session.commit()
            await session.refresh(db_embed_field)

            return await self.get_specific_embed_field(db_embed_field.id, raise_if_not_found=True)

    async def update_embed_fields(self, embed_field: EmbedFieldsUpdate) -> EmbedFieldsSchema:
        async with self.session_factory() as session:
            db_embed_field = await session.get(EmbedFields, embed_field.id, options=[selectinload(EmbedFields.embed)])

            if db_embed_field is None:
                raise EmbedFieldsNotFound(embed_field.id)

            update_data = embed_field.model_dump(exclude_unset=True)

            for field, value in update_data.items():
                setattr(db_embed_field, field, value)

            session.add(db_embed_field)
            await session.commit()
            await session.refresh(db_embed_field)

            return EmbedFieldsSchema.model_validate(db_embed_field)

    async def delete_embed_fields_by_id(self, embed_field_id: int) -> None:
        async with self.session_factory() as session:
            db_embed_field = await session.get(EmbedFields, embed_field_id)

            if db_embed_field is None or db_embed_field.deleted_at is not None:
                raise EmbedFieldsNotFound(embed_field_id)

            db_embed_field.deleted_at = datetime.now(UTC)

            session.add(db_embed_field)
            await session.commit()

    async def delete_embed_fields(self, embed_field: EmbedFieldsSchema) -> None:
        await self.delete_embeds_by_id(embed_field.id)

    async def get_next_position(self, embed_id: int) -> int:
        async with self.session_factory() as session:
            query = (
                select(func.max(EmbedFields.position))
                .where(EmbedFields.embed_id == embed_id)
            )

            result = await session.execute(query)

            max_position = result.scalar()

            current_position = max_position if max_position is not None else 0

            return current_position + 1
