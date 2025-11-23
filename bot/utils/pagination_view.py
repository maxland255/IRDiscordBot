import logging
from typing import Any, Literal, Callable, Union

from discord import EmbedField, Embed, Colour, Interaction
from discord.ui import View, Button, button

logger = logging.getLogger(__name__)


class PaginationView(View):
    """
    A generic pagination view for Discord embeds.
    Attributes:
        data (list[Any]): The list of items to paginate.
        title (str): The title of the embed.
        format_item_func (Callable[[Any], Union[EmbedField, str]]): A function that formats an item into an EmbedField or string.
        items_per_page (int): Number of items to display per page.
        mode (Literal["description", "fields"]): Mode of displaying items, either in the description or as fields.
        embed_color (int | Colour | None): Color of the embed.
    Methods:
        create_page_embed() -> Embed: Creates the embed for the current page.
    """

    def __init__(
            self,
            data: list[Any],
            title: str,
            format_item_func: Callable[[Any], Union[EmbedField, str]],
            items_per_page: int = 5,
            mode: Literal["description", "fields"] = "fields",
            embed_color: int | Colour | None = None,
    ):
        assert mode in ["fields", "description"], "mode must be either 'fields' or 'description'"
        assert not (mode == "fields" and items_per_page > 25), "Discord limits embeds to 25 fields per embed."

        super().__init__(
            timeout=180,
        )

        self.data = data
        self.title = title
        self.format_item_func = format_item_func
        self.items_per_page = items_per_page
        self.mode = mode
        self.embed_color = embed_color

        self.current_page = 0
        self.total_pages = (len(self.data) - 1) // self.items_per_page

        self.update_buttons()

    def create_page_embed(self) -> Embed:
        start_index = self.current_page * self.items_per_page
        end_index = start_index + self.items_per_page

        page_data = self.data[start_index:end_index]

        page_embed = Embed(
            title=self.title,
            colour=self.embed_color,
        )

        page_embed.set_footer(text=f"Page {self.current_page + 1}/{self.total_pages + 1}")

        if not page_data:
            page_embed.description = "No items found."
            return page_embed

        if self.mode == "description":
            lines = [self.format_item_func(item) for item in page_data]
            page_embed.description = "\n".join(lines)
        elif self.mode == "fields":
            page_embed.fields = [self.format_item_func(item) for item in page_data]

        return page_embed

    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.total_pages

    @button(
        label="Previous",
        emoji="⬅️",
    )
    async def previous_button(self, _: Button, interaction: Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            await interaction.response.edit_message(
                embed=self.create_page_embed(),
                view=self,
            )
        else:
            await interaction.response.send_message(
                content="You are already on the first page.",
                ephemeral=True,
            )

    @button(
        label="Next",
        emoji="➡️",
    )
    async def next_button(self, _: Button, interaction: Interaction):
        if self.current_page <= self.total_pages:
            self.current_page += 1
            self.update_buttons()
            await interaction.response.edit_message(
                embed=self.create_page_embed(),
                view=self,
            )
        else:
            await interaction.response.send_message(
                content="You are already on the last page.",
                ephemeral=True,
            )
