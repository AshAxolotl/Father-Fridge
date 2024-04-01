import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Union
from bot_config import EMBED_COLOR

class Quote(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.context_menu = app_commands.ContextMenu(
            name="Quote",
            callback=self.quote_context_menu
        )
        self.bot.tree.add_command(self.context_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.context_menu, type=self.context_menu.type)
        return await super().cog_unload()
    
    async def quote(self, interaction: discord.Interaction, author, text, attachments = []):
        quote_channel_id = await self.bot.pool.fetchval(f"SELECT quote_channel_id FROM settings WHERE guild_id = '{interaction.guild_id}'")
        quote_channel = self.bot.get_partial_messageable(quote_channel_id)

        embed = discord.Embed(
        colour=EMBED_COLOR,
        title=text,
        description=""
        )

        embed.add_field(name=f"-{author.name}", value="", inline=False)
        embed.set_footer(text=f"added by {interaction.user.name}")
        files = []
        for attach in attachments:
                files.append(await attach.to_file())
        
        await quote_channel.send(embed=embed, files=files)
        await interaction.response.send_message(f"Added quote \"{text}\" by {author} in https://discord.com/channels/{interaction.guild_id}/{quote_channel.id}!", ephemeral=True, suppress_embeds=True)
    
    # Quote
    @app_commands.command(name="quote", description="Make a quote in the quote channel (image and/or text required!) (auther is who said the quote)")
    @app_commands.guild_only()
    async def quote_command(self, interaction: discord.Interaction, author: Union[discord.Member ,discord.User], text: Optional[str], image: Optional[discord.Attachment]):
        if image != None:
            await self.quote(interaction, author=author, text=text, attachments=[image])
        else:
            if text != None:
                await self.quote(interaction, author=author, text=text)
            else:
                await interaction.response.send_message("When making a quote pls add text and/or an image", ephemeral=True)
        


    # Context menu
    async def quote_context_menu(self, interaction: discord.Interaction, message: discord.Message) -> None:
        await self.quote(interaction, author=message.author, text=message.content, attachments=message.attachments)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Quote(bot))