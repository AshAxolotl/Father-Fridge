
import discord
from discord import app_commands
from discord.ext import commands

class Funny(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    ## LISTENER
    @commands.Cog.listener()
    async def on_message(self, message:discord.Message):
        # if bot mentioned responed
        if self.bot.user.mentioned_in(message):
            await message.author.send("what doth thee wanteth?")

    ## COMMANDS
    # balls command
    @app_commands.command(name="balls", description="axe asked for this shit")
    async def balls(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"if you want balls just check {interaction.user} browser history")
    
    # echo command
    @app_commands.command(name="echo", description="make the bot say anything... what could go wrong?")
    async def echo(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message(text)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Funny(bot))