import discord
from discord.ext import commands

class SQL(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # add guild to the settings table
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.bot.pool.execute(f"""
            INSERT INTO settings
            (guild_id)
            VALUES ({guild.id});
        """)

    #sql test commands
    @commands.command()
    @commands.is_owner()
    async def sql(self, ctx):
        await ctx.send(f"sql test")

    @sql.error
    async def say_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("thy are not the one that shaped me")
        else:
            print(error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SQL(bot))