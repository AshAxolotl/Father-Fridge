import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Union
import datetime

class Qoute(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
    
    # qoute
    @app_commands.command(name="qoute", description="make a qoute in the qoute channel")
    async def qoute(self, interaction: discord.Interaction, author: Union[discord.Member ,discord.User], text: Optional[str], image: Optional[discord.Attachment]):
        qoute_channel = interaction.guild.get_channel(self.bot.data["quoteChannel"])

        embed = discord.Embed(
        colour=discord.Colour.dark_gold(),
        title=text,
        description = ""
        )

        embed.set_author(name=f"-{author.name}", icon_url=author.avatar)
        embed.set_footer(text=f"added by {interaction.user.name}")
        if isinstance(image, discord.message.Attachment):
            embed.set_image(url=image)
        
        else:
            if not isinstance(text, str):
                await interaction.response.send_message("When making a qoute pls add text and/or an image", ephemeral=True)
                return
        
        

        await qoute_channel.send(embed=embed)
        await interaction.response.send_message(f"Added qoute \"{text}\" by {author} in #{qoute_channel}!", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(Qoute(bot))