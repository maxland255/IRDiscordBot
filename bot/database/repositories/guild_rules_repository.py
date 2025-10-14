from typing import Protocol, Union, List
from abc import abstractmethod
from datetime import datetime, UTC

from bot.database.models import GuildRules
from bot.exception import GuildRuleNotFound
from bot.database.schemas import GuildRulesCreate, GuildRulesSchema, GuildRulesUpdate

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker


class GuildRulesRepository(Protocol):
    """
    Declare all methods used by the bot to interact with the database.
    The data could be from a database or an api.
    """

    @abstractmethod
    async def get_guild_rules(self, guild_id: int) -> List[GuildRulesSchema]:
        """
        Get all Guild Rules data.
        :param guild_id:
        :return:
        """
        ...

    @abstractmethod
    async def get_specific_guild_rules(self, rule_id: int, raise_if_not_found: bool = False) -> Union[
        GuildRulesSchema, None]:
        """
        Get specific Guild Rules data.
        :param rule_id:
        :param raise_if_not_found:
        :return:
        """
        ...

    @abstractmethod
    async def guild_rules_require_publish(self, guild_id: int) -> bool:
        """
        Get if guild rules require publication.
        :param guild_id:
        :return:
        """
        ...

    @abstractmethod
    async def create_guild_rules(self, guild_rules: GuildRulesCreate) -> GuildRulesSchema:
        """
        Create a Guild Rules.
        :param guild_rules:
        :return:
        """
        ...

    @abstractmethod
    async def update_guild_rules(self, guild_rules: GuildRulesUpdate) -> GuildRulesSchema:
        """
        Update a Guild Rules.
        :param guild_rules:
        :return:
        """
        ...

    @abstractmethod
    async def delete_guild_rules(self, guild_rules_id: int) -> bool:
        """
        Safe delete a Guild Rules.
        :param guild_rules_id:
        :return:
        """
        ...


class SQLAlchemyGuildRulesRepository(GuildRulesRepository):
    def __init__(self, session_factory: async_sessionmaker):
        self.session_factory = session_factory

    async def get_guild_rules(self, guild_id: int) -> List[GuildRulesSchema]:
        async with self.session_factory() as session:
            result = await session.execute(
                select(GuildRules)
                .where(GuildRules.guild_id == guild_id)
                .where(GuildRules.deleted_at.is_(None))
            )

            db_guild_rules = result.scalars().all()

            return [GuildRulesSchema.model_validate(guild_rule) for guild_rule in db_guild_rules]

    async def get_specific_guild_rules(self, rule_id: int, raise_if_not_found: bool = False) -> Union[
        GuildRulesSchema, None]:
        async with self.session_factory() as session:
            db_guild_rule = await session.get(GuildRules, rule_id)

            if db_guild_rule is None:
                if raise_if_not_found:
                    raise GuildRuleNotFound(rule_id)
                else:
                    return None

            return GuildRulesSchema.model_validate(db_guild_rule)

    async def guild_rules_require_publish(self, guild_id: int) -> bool:
        async with self.session_factory() as session:
            result = await session.execute(
                select(GuildRules)
                .where(GuildRules.guild_id == guild_id)
                .where(GuildRules.rules_require_publish == True)
            )

            guild_rules = result.scalars().all()

            return len(guild_rules) > 0

    async def create_guild_rules(self, guild_rules: GuildRulesCreate) -> GuildRulesSchema:
        async with self.session_factory() as session:
            db_guild_rules = GuildRules(**guild_rules.model_dump())

            session.add(db_guild_rules)
            await session.commit()
            await session.refresh(db_guild_rules)

            return GuildRulesSchema.model_validate(db_guild_rules)

    async def update_guild_rules(self, guild_rules: GuildRulesUpdate) -> GuildRulesSchema:
        async with self.session_factory() as session:
            db_guild_rules = await session.get(GuildRules, guild_rules.id)

            if db_guild_rules is None:
                raise GuildRuleNotFound(guild_rules)

            update_data = guild_rules.model_dump(exclude_unset=True)

            for key, value in update_data.items():
                setattr(db_guild_rules, key, value)

            session.add(db_guild_rules)
            await session.commit()
            await session.refresh(db_guild_rules)

            return GuildRulesSchema.model_validate(db_guild_rules)

    async def delete_guild_rules(self, guild_rules_id: int) -> bool:
        async with self.session_factory() as session:
            db_guild_rules = await session.get(GuildRules, guild_rules_id)

            if db_guild_rules is None:
                return False

            db_guild_rules.deleted_at = datetime.now(UTC)

            session.add(db_guild_rules)
            await session.commit()

            return True
