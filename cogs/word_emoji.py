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

    if word not in self.bot.data["wordEmojis"]:
      self.bot.data["wordEmojis"][word] = []

    if emoji not in self.bot.data["wordEmojis"][word] and len(self.bot.data["wordEmojis"][word]) < 10:
      self.bot.data["wordEmojis"][word].append(emoji)
      write_json_data(self.bot.data)
      await interaction.response.send_message(f"{emoji} will get added on word: {word}")
    else:
      await interaction.response.send_message(f"{emoji} already gets added to {word} or the word {word} already has 10 emojis", ephemeral=True)
    
    
    

async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(WordEmoji(bot))

# json write (for cogs)
def write_json_data(data):
  data_json = json.dumps(data)
  with open("data.json", "w") as file:
    file.write(data_json)