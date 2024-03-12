import discord
from discord.ext import commands

class MiscellaneousEvents(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # on member join
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        # Join Role
        role_id = await self.bot.pool.fetchval(f"SELECT join_role_id FROM settings WHERE guild_id = '{member.guild.id}'")
        if role_id is not None:
            role = member.guild.get_role(role_id)
            await member.add_roles(role, reason="Joined guild")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MiscellaneousEvents(bot))



