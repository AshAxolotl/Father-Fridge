import discord
from discord.ext import commands
from bot_config import OWNER_USERIDS

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
            
    
    @sync_cmds.error
    async def say_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("thy are not the one that shaped me")

    #shutdown bot
    @commands.command()
    @commands.is_owner()
    async def shutdown(self, ctx):
            print("Shutting Down from command")
            await ctx.send("Shutting Down")
            await self.bot.pool.close()
            await self.bot.close()
    
    @shutdown.error
    async def say_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("thy are not the one that shaped me")



async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(OwnerCommands(bot))
