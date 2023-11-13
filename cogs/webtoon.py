import discord
from discord import app_commands
from discord.ext import commands
import json
import random

class Webtoon(commands.GroupCog, name="webtoon"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required in this context.

    # webtoon 
    @app_commands.command(name="get", description="sends you a webtoon recommendation THAT YOU SHALL READ")
    async def webtoon(self, interaction: discord.Interaction):
        randomWebtoon = random.choice(self.bot.data["webtoons"])
        await interaction.response.send_message(f"I think you should read {randomWebtoon} but I exist in every instance of time so I do not know what you have read",ephemeral=True)


    # recommand webtoon 
    @app_commands.command(name="add", description="sends you a webtoon recommendation THAT YOU SHALL READ")
    async def recommand_webtoon(self, interaction: discord.Interaction, webtoon: str):
        if webtoon.startswith("https://www.webtoons.com/en/") and "list?title_no" in webtoon:
            if webtoon in self.bot.data["webtoons"]:
                await interaction.response.send_message("I already know this!",ephemeral=True)
            else:
                self.bot.data["webtoons"].append(webtoon)
                write_json_data(self.bot.data)
                await interaction.response.send_message(f"{webtoon} has been added to my infinite knowledge",ephemeral=True)
        else:
            await interaction.response.send_message("Thats not a webtoon you befoon (also make sure that it isnt a link to a chapter!))",ephemeral=True)

   
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Webtoon(bot))

# json write (for cogs)
def write_json_data(data):
  data_json = json.dumps(data)
  with open("data.json", "w") as file:
    file.write(data_json)