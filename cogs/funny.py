
import discord
from discord import app_commands
from discord.ext import commands

class Funny(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    # balls
    @app_commands.command(name="balls", description="axe asked for this shit")
    async def balls(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"if you want balls just check {interaction.user} browser history")

async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(Funny(bot))