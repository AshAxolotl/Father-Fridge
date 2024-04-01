# Importing Dependencies
import os.path
import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncpg
from bot_config import TOKEN, DEBUG, OWNER_USERIDS, COMMAND_PREFIX, SQL_IP, SQL_USER, SQL_PASSWORD, SQL_PORT, NO_PERMS_MESSAGE


# Bot Activity
if DEBUG:
    activity = discord.CustomActivity(name="IN DEV")
    status = discord.Status.dnd
    log_level = logging.DEBUG
else:
    activity = discord.Activity(name="over all", type=discord.ActivityType.watching)
    status = discord.Status.online
    log_level = logging.ERROR


class CustomCommandTree(app_commands.CommandTree):
    # app command errors
    async def on_error(self, interaction: discord.Interaction[discord.Client], error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE.format(error = error).replace("[", "").replace("]", ""), ephemeral=True)
        else:
            return await super().on_error(interaction, error)


class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or(COMMAND_PREFIX), intents=discord.Intents.all(), activity=activity, status=status, tree_cls=CustomCommandTree)
        self.owner_ids.update(OWNER_USERIDS)

    async def setup_hook(self) -> None:
        # Database
        self.pool = await asyncpg.create_pool(dsn=f"postgres://{SQL_USER}:{SQL_PASSWORD}@{SQL_IP}:{SQL_PORT}/fatherfridgedb")

        # load extensions / cogs
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await bot.load_extension(f"cogs.{filename[:-3]}")

    async def on_ready(self):
        print(f"{self.user} is CONNECTED!")
        print("--------------")

    # ctx command errors
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.NotOwner):
            await ctx.send("thy are not the one that shaped me")
        else:
            return await super().on_command_error(ctx, error)


# Setting up Discord Bot Manager Class and Command Handler
bot = CustomBot()

bot.run(TOKEN, log_handler=logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w'), log_level=log_level)