from bot.database.schemas import GuildSchema, GuildUpdate, GravityLevelSchema, GravityLevelUpdate, GravityLevelCreate, \
    InfractionsUpdate, InfractionsSchema, InfractionsCreate, GuildRulesSchema, GuildRulesUpdate, RolePanelSchema, \
    RolePanelUpdate, RoleOptionsUpdate, ReportSchema
from typing import Union


class GuildNotFound(Exception):
    def __init__(self, guild: Union[int, GuildSchema, GuildUpdate]) -> None:
        self.guild = guild

    def __str__(self) -> str:
        if isinstance(self.guild, int):
            return f"Guild {self.guild} not found"
        return f"Guild {self.guild.id} | {self.guild.name} not found"


class GravityLevelNotFound(Exception):
    def __init__(self,
                 gravity_level: Union[int, str, GravityLevelSchema, GravityLevelUpdate, GravityLevelCreate]) -> None:
        self.gravity_level = gravity_level

    def __str__(self) -> str:
        if isinstance(self.gravity_level, int):
            return f"Gravity Level {self.gravity_level} not found"

        if isinstance(self.gravity_level, str):
            return f"Gravity Level {self.gravity_level} not found"

        return f"Gravity Level {self.gravity_level.id} | {self.gravity_level.name} not found"


class InfractionNotFound(Exception):
    def __init__(self, infraction: Union[int, InfractionsUpdate, InfractionsSchema, InfractionsCreate]) -> None:
        self.infraction = infraction

    def __str__(self) -> str:
        if isinstance(self.infraction, int):
            return f"Infraction {self.infraction} not found"

        return f"Infraction {self.infraction.id} | {self.infraction.infraction_type.name} not found"


class GuildRuleNotFound(Exception):
    def __init__(self, guild_rule: Union[int, GuildRulesSchema, GuildRulesUpdate]) -> None:
        self.guild_rule = guild_rule

    def __str__(self) -> str:
        if isinstance(self.guild_rule, int):
            return f"Guild Rule {self.guild_rule} not found"

        return f"Guild Rule {self.guild_rule.id} | {self.guild_rule.name} not found"


class RolesPanelNotFound(Exception):
    def __init__(self, panel_id: Union[int, RolePanelSchema, RolePanelUpdate]) -> None:
        self.panel_id = panel_id

    def __str__(self) -> str:
        if isinstance(self.panel_id, int):
            return f"Roles Panel {self.panel_id} not found"

        return f"Roles Panel {self.panel_id.id} | {self.panel_id.name} not found"


class RoleOptionsNotFound(Exception):
    def __init__(self, role_options: Union[int, RoleOptionsUpdate]) -> None:
        self.role_options = role_options

    def __str__(self) -> str:
        if isinstance(self.role_options, int):
            return f"Roles Panel {self.role_options} not found"

        return f"Roles Panel {self.role_options.id} | {self.role_options.label} not found"


class ReportNotFound(Exception):
    def __init__(self, report: Union[int, ReportSchema]) -> None:
        self.report = report

    def __str__(self) -> str:
        if isinstance(self.report, int):
            return f"Report {self.report} not found"

        return f"Report {self.report.id} not found"
