import logging
import discord

from discord import app_commands
from discord.ext import commands

import util.command_helper
from tasks.promote_task import PromoteTask


class RunCommand(commands.GroupCog, name="run"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(name="promotions", description="Calculates weekly GEXP and promotes members")
    async def promotion_task(self, interaction: discord.Interaction, flags: str=None):
        if not util.command_helper.check_permission(interaction.user, level="any"):
            await interaction.response.send_message(embed=util.command_helper.no_perm_embed())
        promotions_task = PromoteTask()
        await promotions_task.run(interaction)
        if promotions_task.errored:
            await interaction.response.send_message(embed=promotions_task.error_embed)


async def setup(bot) -> None:
    logging.debug("Adding cog: RunCommand")
    await bot.add_cog(RunCommand(bot))
