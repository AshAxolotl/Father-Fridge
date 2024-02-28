import discord
from discord import app_commands
from discord.ext import commands
import json
from typing import Optional
import datetime
import time

class Poll(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot
    
    #poll create
    @app_commands.command(name="poll", description="basic poll command")
    async def poll(self, interaction:discord.Interaction, question: str, options: str, unix_endtime: Optional[int] = None):
        
        options = options.split(", ")
        # emojis only work from 1-9 so check
        if len(options) > 9:
            await interaction.response.send_message("To many options! (max 9)", ephemeral=True)
            return
        
        # text for view description
        options_text: str = ""
        for i in range(len(options)):
            emoji = str(i + 1) + "\ufe0f\u20e3"
            options_text += f"{emoji} {options[i]}\n"


        # view
        embed = discord.Embed(
        colour=discord.Colour.dark_gold(),
        title=question,
        description=options_text,
        )

        # end time
        if isinstance(unix_endtime, int):
            d = datetime.datetime.now()
            unixtime = time.mktime(d.timetuple())
            unixtime += float(unix_endtime)

            # makes sure the poll doesnt end in over a 14 days
            if unix_endtime > 1209600:
                await interaction.response.send_message("im not keeping a poll open for that long >:(")
                return
            
            embed.set_footer(text="Ends at")
            embed.timestamp = datetime.datetime.fromtimestamp(unixtime)
        
        
        
        
        await interaction.response.send_message(embed=embed)
        
        #adds emojis to the message
        message = await interaction.original_response()
        for i in range(len(options)):
            emoji = str(i + 1) + "\ufe0f\u20e3"
            await message.add_reaction(emoji)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Poll(bot))