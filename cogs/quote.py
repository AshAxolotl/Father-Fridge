import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Union

class Quote(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
    
    # Quote
    @app_commands.command(name="quote", description="make a quote in the quote channel")
    async def quote(self, interaction: discord.Interaction, author: Union[discord.Member ,discord.User], text: Optional[str], image: Optional[discord.Attachment]):
        quote_channel_id = await self.bot.pool.fetchval(f"SELECT quote_channel_id FROM settings WHERE guild_id = '{interaction.guild_id}'")
        quote_channel = interaction.guild.get_channel(quote_channel_id)

        embed = discord.Embed(
        colour=discord.Colour.dark_gold(),
        title=text,
        description=""
        )

        embed.add_field(name=f"-{author.name}", value="", inline=False)
        # embed.set_author(name=f"-{author.name}", icon_url=author.avatar)
        embed.set_footer(text=f"added by {interaction.user.name}")
        if isinstance(image, discord.message.Attachment):
            embed.set_image(url=image)
        
        else:
            if not isinstance(text, str):
                await interaction.response.send_message("When making a quote pls add text and/or an image", ephemeral=True)
                return
        
        

        await quote_channel.send(embed=embed)
        await interaction.response.send_message(f"Added quote \"{text}\" by {author} in https://discord.com/channels/{interaction.guild_id}/{quote_channel.id}!", ephemeral=True, suppress_embeds=True)


async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(Quote(bot))