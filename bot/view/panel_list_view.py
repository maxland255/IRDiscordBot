from discord import Embed, Color, Interaction
from discord.ui import View, Button, button

from bot.database.schemas import RolePanelSchema


class RolePanelListView(View):
    def __init__(self, panels: list[RolePanelSchema], item_per_page: int = 5):
        super().__init__(timeout=180)
        self.panels = panels
        self.item_per_page = item_per_page
        self.current_page = 0
        self.total_pages = (len(self.panels) - 1) // self.item_per_page

    def create_page_embed(self) -> Embed:
        start_index = self.current_page * self.item_per_page
        end_index = start_index + self.item_per_page

        page_panels = self.panels[start_index:end_index]

        page_embed = Embed(
            title=f"Role Panel List (Page {self.current_page + 1}/{self.total_pages + 1})",
            colour=Color.blue(),
        )

        for panel in page_panels:
            page_embed.add_field(
                name=panel.name,
                value=f"ID: {panel.id}\nTitle: {panel.title}",
                inline=False,
            )

        if len(page_panels) <= 0:
            page_embed.description = "No role panels found."

        return page_embed

    async def update_message(self, interaction: Interaction):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.total_pages

        await interaction.response.edit_message(
            embed=self.create_page_embed(),
            view=self,
        )

    @button(
        label="Previous",
        emoji="⬅️",
    )
    async def previous_button(self, _: Button, interaction: Interaction):
        if self.current_page > 0:
            self.current_page -= 1
            await self.update_message(interaction)

    @button(
        label="Next",
        emoji="➡️",
    )
    async def next_button(self, _: Button, interaction: Interaction):
        if self.current_page < self.total_pages:
            self.current_page += 1
            await self.update_message(interaction)
