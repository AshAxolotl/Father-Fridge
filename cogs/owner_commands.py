import discord
from discord.ext import commands
from bot_config import OWNER_USERIDS, DEBUG

class OwnerCommands(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    #sync commands
    @commands.command()
    @commands.is_owner()
    async def sync_cmds(self, ctx):
        print("Synced Commands")
        await self.bot.tree.sync()
        await ctx.send("Command tree sycned")

    #shutdown bot
    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
            print("Shutting Down from command")
            await ctx.send("Shutting Down")
            await self.bot.pool.close()
            await self.bot.close()

    #send log
    @commands.command()
    @commands.is_owner()
    async def log(self, ctx: commands.Context):
        log_file = discord.File("discord.log", filename="dicord.log")
        await ctx.send(f"DEBUG: {DEBUG}",file=log_file)



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OwnerCommands(bot))
