import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="help me I dumb")
    async def reaction_role_list(self, interaction:discord.Interaction):
        await interaction.response.send_message("uhhhh to lazy to wright anything. if you need help just like call 112 or 113?", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))