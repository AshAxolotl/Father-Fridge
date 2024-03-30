# Importing Dependencies
import os.path
import discord
from discord.ext import commands
import logging
import asyncpg
from bot_config import TOKEN, DEBUG, OWNER_USERIDS, COMMAND_PREFIX, SQL_IP, SQL_USER, SQL_PASSWORD, SQL_PORT


# Bot Activity
if DEBUG:
    activity = discord.CustomActivity(name="IN DEV")
    status = discord.Status.dnd
    log_level = logging.DEBUG
else:
    activity = discord.Activity(name="over all", type=discord.ActivityType.watching)
    status = discord.Status.online
    log_level = logging.ERROR


# Setting up Discord Bot Manager Class and Command Handler
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all(), activity=activity, status=status) #, activity=activity, status=status
bot.owner_ids.update(OWNER_USERIDS)

# cog loading
async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


## BOT EVENTS
# setup hooks
@bot.event
async def setup_hook():
    # Database
    bot.pool = await asyncpg.create_pool(dsn=f"postgres://{SQL_USER}:{SQL_PASSWORD}@{SQL_IP}:{SQL_PORT}/fatherfridgedb")
    await bot.pool.execute("""
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
    # load extensions / cogs
    await load_extensions()

# start up message
@bot.event
async def on_ready():
    print(f"{bot.user} is CONNECTED!")
    print("--------------")


## CONTEXT MENUS (dont have good cog support so they here)
# Quote context menu
@bot.tree.context_menu(name="quote")
async def quote(interaction: discord.Interaction, message: discord.Message):
    quote_channel = interaction.guild.get_channel(bot.data["quoteChannel"])

    embed = discord.Embed(
    colour=discord.Colour.dark_gold(),
    title=message.content,
    description=""
    )

    embed.add_field(name=f"-{message.author.name}", value="", inline=False)

    embed.set_footer(text=f"added by {interaction.user.name}")

    await quote_channel.send(embed=embed)
    await interaction.response.send_message(f"Added quote \"{message.content}\" by {message.author.name} in #{quote_channel}!", ephemeral=True)



bot.run(TOKEN, log_handler=logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w'), log_level=log_level)