import logging

from typing import Callable, Coroutine, Any

from discord import ButtonStyle, Interaction
from discord.ui import Button

CallbackType = Callable[[Interaction], Coroutine[Any, Any, None]]

logger = logging.getLogger(__name__)


class ActionButton(Button):
    def __init__(
            self,
            *,
            style: ButtonStyle = ButtonStyle.secondary,
            label: str,
            emoji: str | None = None,
            custom_id: str | None = None,
            on_click: CallbackType,
    ):
        super().__init__(
            style=style,
            label=label,
            emoji=emoji,
            custom_id=custom_id,
        )

        self.on_click_callback = on_click

    async def callback(self, interaction: Interaction):
        try:
            await self.on_click_callback(interaction)
        except Exception as e:
            logger.exception("Error occurred in ActionButton callback", exc_info=e)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "An error occurred while processing your request.",
                    ephemeral=True,
                )
