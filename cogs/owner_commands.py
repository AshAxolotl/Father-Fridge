import discord
from discord.ext import commands
import json
from bot_config import OWNER_USERIDS

class OwnerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    #sync commands
    @commands.command()
    async def sync_cmds(self, ctx):
        if ctx.author.id in OWNER_USERIDS:
            print("Synced Commands")
            await self.bot.tree.sync()
            await ctx.send("Command tree sycned")
        else:
            await ctx.send("thy are not the one that shaped me")

    #shutdown bot
    @commands.command()
    async def shutdown(self, ctx):
        if ctx.author.id in OWNER_USERIDS:
            print("Shutting Down from command")
            await ctx.send("Shutting Down")
            write_json_data(self.bot.data)
            await self.bot.pool.close()
            await self.bot.close()
        else:
            await ctx.send("thy are not the one that shaped me")



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OwnerCommands(bot))

# json write (for cogs)
def write_json_data(data):
    data_json = json.dumps(data, indent=4)
    with open("data.json", "w") as file:
        file.write(data_json)