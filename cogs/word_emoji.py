import discord
from discord import app_commands
from discord.ext import commands
import json
from typing import Optional


class WordEmoji(commands.GroupCog, name="wmoji"):
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot
    super().__init__()

  #word emoji add
  @app_commands.command(name="add", description="make the bot react with a emoji on a word")
  async def wmoji_add(self, interaction:discord.Interaction, word:str, emoji:str):
    word = word.lower()

    #checks if its longer then 3 chaters
    if len(word) < 3:
      await interaction.response.send_message(f"{word} is shoter then 3 character!", ephemeral=True)
      return

    if word not in self.bot.data["wordEmojis"]:
      self.bot.data["wordEmojis"][word] = []

    if emoji not in self.bot.data["wordEmojis"][word] and len(self.bot.data["wordEmojis"][word]) < 10:
      self.bot.data["wordEmojis"][word].append(emoji)
      write_json_data(self.bot.data)
      await interaction.response.send_message(f"{emoji} will get added on word: {word}")
    else:
      await interaction.response.send_message(f"{emoji} already gets added to {word} or the word {word} already has 10 emojis", ephemeral=True)
    
  #word emoji remove
  @app_commands.command(name="remove", description="stops the bot from reacting with a emoji on a word")
  async def wmoji_remove(self, interaction:discord.Interaction, word:str, emoji: Optional[str]):
    word = word.lower()

    if type(emoji) == str:
      self.bot.data["wordEmojis"][word].remove(emoji)
      await interaction.response.send_message(f"removed {emoji} from being reacted on word: {word}")
    else:

      del self.bot.data["wordEmojis"][word]
      await interaction.response.send_message(f"removed ALL emojis from being reacted on word {word}")
    
    write_json_data(self.bot.data)

  #word emoji list
  @app_commands.command(name="list", description="list of wmoji")
  async def wmoji_list(self, interaction:discord, word: Optional[str]):
    text = ""
    if word == None:
      title = "wmoji: ALL"
      for key in self.bot.data["wordEmojis"]:
        text += f"{key}: "
        for emoji in self.bot.data["wordEmojis"][key]:
          text += f"{emoji} "
        text += "\n"
    else: 
      word.lower()
      title = "wmoji: " + word
      if word in self.bot.data["wordEmojis"]:
        for emoji in self.bot.data["wordEmojis"][word]:
          text += f"{emoji} "
      else:
        text = f"HAS NONE"

    embed = discord.Embed(
      colour=discord.Colour.gold(),
      title=title,
      description=text,
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

    
    
    

async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(WordEmoji(bot))

# json write (for cogs)
def write_json_data(data):
  data_json = json.dumps(data)
  with open("data.json", "w") as file:
    file.write(data_json)