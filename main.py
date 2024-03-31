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
    async def on_error(self, interaction: discord.Interaction[discord.Client], error: app_commands.AppCommandError) -> None:
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True)
        else:
            return await super().on_error(interaction, error)


class CustomBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all(), activity=activity, status=status, tree_cls=CustomCommandTree)
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

    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(error, commands.NotOwner):
            await ctx.send("thy are not the one that shaped me")
        else:
            return await super().on_command_error(ctx, error)


# Setting up Discord Bot Manager Class and Command Handler
bot = CustomBot()

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