from typing import Optional

from datetime import datetime, timedelta, UTC

from bot.database.schemas import InfractionType, InfractionsSchema, GravityLevelSchema, GuildSchema


async def calculate_timeout_duration(infractions: list[InfractionsSchema],
                                     guild_config: GuildSchema, gravity_level: GravityLevelSchema | None = None,
                                     weight: int | None = None) -> Optional[datetime]:
    """
    Calculate the timeout duration based on the user's infractions and gravity level.
    :param infractions:
    :param guild_config:
    :param gravity_level:
    :param weight:
    :return:
    """

    assert (gravity_level is not None) != (weight is not None), \
        "Either gravity_level or weight must be provided, but not both."

    history_weight = 0.0
    for infraction in infractions:
        if infraction.infraction_type == InfractionType.warn:
            history_weight += guild_config.warn_height
        elif infraction.infraction_type == InfractionType.timeout:
            history_weight += infraction.gravity.weight

    if weight is not None:
        WARN_TIMEOUT_THRESHOLD = 1.0

        if history_weight < WARN_TIMEOUT_THRESHOLD:
            return None

        current_infractions_weight = weight
    else:
        current_infractions_weight = gravity_level.weight

    base_duration = guild_config.default_timeout

    final_multiplier = 1.0 + history_weight

    timeout_seconds = base_duration * current_infractions_weight * final_multiplier

    max_discord_timeout = 28 * 24 * 3600
    timeout_seconds = min(timeout_seconds, max_discord_timeout)

    until = datetime.now(UTC) + timedelta(seconds=timeout_seconds)

    return until
