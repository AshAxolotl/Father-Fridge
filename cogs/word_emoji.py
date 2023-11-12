import discord
from discord import app_commands
from discord.ext import commands
import json


class WordEmoji(commands.Cog):
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot

  @app_commands.command(name="word_emoji", description="make the bot react with a emoji on a word")
  async def word_emoji(self, interaction:discord.Interaction, word:str, emoji:str):
    word = word.lower()
    await interaction.response.send_message(f"{emoji} will get added on word: {word}")
    self.bot.data["wordEmojis"][word] = emoji
    write_json_data(self.bot.data)

async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(WordEmoji(bot))

# json write (for cogs)
def write_json_data(data):
    data_json = json.dumps(data)
    with open("data.json", "w") as file:
        file.write(data_json)