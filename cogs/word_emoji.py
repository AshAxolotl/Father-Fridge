import discord
from discord import app_commands
from discord.ext import commands
import json
from typing import Optional


class WordEmoji(commands.GroupCog, name="wmoji"):
  def __init__(self, bot: commands.Bot) -> None:
    self.bot = bot
    super().__init__()


  ## LISTENER
  @commands.Cog.listener()
  async def on_message(self, message:discord.Message): 
    if message.author != self.bot.user:
      emojis_records = await self.bot.pool.fetch(f"""
      SELECT emoji FROM wmojis
      WHERE guild_id = {message.guild.id} AND $1 LIKE '%' || word || '%';
      """, message.content.lower())

      for emoji_record in emojis_records:
        await message.add_reaction(emoji_record["emoji"])
      

  ## COMMANDS
  #word emoji add
  @app_commands.command(name="add", description="make the bot react with a emoji on a word")
  async def wmoji_add(self, interaction:discord.Interaction, word:str, emoji:str):
    word = word.lower()

    #checks if its longer then 3 chaters
    if len(word) < 3:
      await interaction.response.send_message(f"{word} is shoter then 3 character!", ephemeral=True)
      return
    
    # check for emoji (TODO this could be beter)
    if " " in emoji:
      await interaction.response.send_message(f"{emoji} is not valid!", ephemeral=True)
      return

    current_wmojis_records = await self.bot.pool.fetch(f"""
      SELECT emoji FROM wmojis
      WHERE guild_id = {interaction.guild_id} AND word = $1;
    """, word)

    # check if there are already 10 emojis on the word
    if len(current_wmojis_records) >= 10:
      await interaction.response.send_message(f"There are already 10 emojis on word {word}!", ephemeral=True)
      return
    
    for current_wmoji_record in current_wmojis_records:
      if emoji in current_wmoji_record["emoji"]:
        await interaction.response.send_message(f"{emoji} already gets added to {word}", ephemeral=True)
        return

    await self.bot.pool.execute(f"""
      INSERT INTO wmojis
      (guild_id, word, emoji)
      VALUES ({interaction.guild_id}, $1, $2); 
    """, word, emoji) 
    await interaction.response.send_message(f"{emoji} will get added on word: {word}")


  #word emoji remove
  @app_commands.command(name="remove", description="stops the bot from reacting with a emoji on a word")
  async def wmoji_remove(self, interaction: discord.Interaction, word: str, emoji: Optional[str]):
    word = word.lower()

    if type(emoji) == str:
      await self.bot.pool.execute("DELETE FROM wmojis WHERE $1 = word AND emoji = $2;", word.lower(), emoji)
      await interaction.response.send_message(f"removed {emoji} from being reacted on word: {word}")
    else:

      await self.bot.pool.execute("DELETE FROM wmojis WHERE $1 = word;", word.lower())
      await interaction.response.send_message(f"removed ALL emojis from being reacted on word {word}")


  #word emoji list
  @app_commands.command(name="list", description="get a list of wmoji's")
  async def wmoji_list(self, interaction: discord.Interaction, word: Optional[str]):
    if word == None:
      title = "wmoji: ALL"
      records = await self.bot.pool.fetch(f"""
        SELECT word, emoji FROM wmojis
        WHERE guild_id = {interaction.guild_id}
        ORDER BY word ASC; 
        """)

    else:
      word.lower()
      title = f"wmoji: {word}"

      records = await self.bot.pool.fetch(f"""
      SELECT word, emoji FROM wmojis
      WHERE guild_id = {interaction.guild_id}
        AND $1 LIKE '%' || word || '%'
      ORDER BY word ASC;
      """, word)

    text = ""
    if len(records) > 0:
      current_word = ""
      for record in records:
        if record["word"] != current_word:
          text += f"\n{record['word']}: "
          current_word = record["word"]
        
        text += f"{record['emoji']} "
    else:
      text += "N/A"

    embed = discord.Embed(
      colour=discord.Colour.dark_gold(),
      title=title,
      description=text,
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

    

async def setup(bot: commands.Bot) -> None:
  await bot.add_cog(WordEmoji(bot))