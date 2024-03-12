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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SQL(bot))




# removed for now
"""
        CREATE TABLE IF NOT EXISTS art_contests (
            guild_id BIGINT PRIMARY KEY,
            art_contest_theme TEXT,
            art_contest_role_id BIGINT,
            art_contest_announcements_channel_id BIGINT,
            art_contest_submissions_channel_id BIGINT,
            art_contest_theme_suggestion_channel_id BIGNIT,
            art_contest_poll_message_id BIGINT,
            art_contest_form_id BIGINT,
            art_contest_responder_uri TEXT
        );
"""