import discord
from discord import app_commands
from discord.ext import commands
import json
import random
from typing import Optional

class Webtoon(commands.GroupCog, name="webtoon"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required in this context.

    # webtoon 
    @app_commands.command(name="get", description="sends you a webtoon recommendation THAT YOU SHALL READ")
    async def webtoon(self, interaction: discord.Interaction, amount: Optional[app_commands.Range[int, 1, 20]] = 3):
        #makes a list of webtoons of the spified amount
        webtoon_list = []
        webtoon_data_copy = [] 
        webtoon_data_copy.extend(self.bot.data["webtoons"])
        for i in range(amount):
            if not webtoon_data_copy:
                break
            randomWebtoon = random.choice(webtoon_data_copy)
            webtoon_list.append(randomWebtoon)
            webtoon_data_copy.remove(randomWebtoon)
        
        #makes a string out of the list
        webtoon_msg = "Here is a list of webtoons that i know of: \n"
        for webtoon in webtoon_list:
            webtoon_msg = webtoon_msg + webtoon + "\n"
        webtoon_msg = webtoon_msg + "only up to 5 will show up as embeds!"

        await interaction.response.send_message(webtoon_msg,ephemeral=True)


    # recommand webtoon 
    @app_commands.command(name="add", description="add a webtoon to the database")
    async def recommand_webtoon(self, interaction: discord.Interaction, webtoon: str):
        if not webtoon.startswith("https://www.webtoons.com/en/") and not "list?title_no" in webtoon:
            await interaction.response.send_message("Thats not a webtoon you befoon (also make sure that it isnt a link to a chapter!))",ephemeral=True)
            return
        
        if webtoon in self.bot.data["webtoons"]:
            await interaction.response.send_message("I already know this!",ephemeral=True)
            return
        
        self.bot.data["webtoons"].append(webtoon)
        write_json_data(self.bot.data)
        await interaction.response.send_message(f"{webtoon} has been added to my infinite knowledge",ephemeral=True)

   
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Webtoon(bot))

# json write (for cogs)
def write_json_data(data):
  data_json = json.dumps(data)
  with open("data.json", "w") as file:
    file.write(data_json)