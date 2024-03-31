import discord
from discord.ext import commands

class SQL(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def cog_load(self):
        await self.bot.pool.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                guild_id BIGINT PRIMARY KEY,
                join_role_id BIGINT,
                quote_channel_id BIGINT,
                art_contest_theme TEXT,
                art_contest_role_id BIGINT,
                art_contest_announcements_channel_id BIGINT,
                art_contest_poll_message_id BIGINT,
                art_contest_theme_suggestion_channel_id BIGINT,
                art_contest_theme_suggestions_message_id BIGINT,
                art_contest_submissions_channel_id BIGINT,
                art_contest_form_id TEXT,
                art_contest_responder_uri TEXT
            );
            CREATE TABLE IF NOT EXISTS wmojis (
                guild_id BIGINT,
                word TEXT,
                emoji TEXT
            );
            CREATE TABLE IF NOT EXISTS reaction_roles (
                guild_id BIGINT,
                message_id BIGINT,
                emoji TEXT,
                role_id BIGINT,
                channel_id BIGINT
            );
            CREATE TABLE IF NOT EXISTS server_name_suggestions (
                guild_id BIGINT,
                user_id BIGINT,
                name_suggestion TEXT,
                UNIQUE (guild_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS art_contest_theme_suggestions (
                guild_id BIGINT,
                user_id BIGINT,
                suggested_theme TEXT,
                UNIQUE (guild_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS art_contest_submissions (
                guild_id BIGINT,
                user_id BIGINT,
                thread_id BIGINT,
                message_id BIGINT,
                form_id TEXT,
                title TEXT,
                image_url TEXT,
                UNIQUE (guild_id, user_id)
            );
        """)


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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SQL(bot))