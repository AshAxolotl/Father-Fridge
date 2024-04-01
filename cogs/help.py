import discord
from discord import app_commands
from discord.ext import commands
from bot_config import EMBED_COLOR

class CustomHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page, color=EMBED_COLOR, title="ALL IMPORTANT COMMANDS ARE APP (/) COMMANDS!")
            await destination.send(embed=emby)

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self
    
    def cog_unload(self):
        self.bot.help_command = self._original_help_command

    @app_commands.command(name="help", description="Help me I dumb")
    async def reaction_role_list(self, interaction:discord.Interaction):

        embed = discord.Embed(
        description="", # Commands are sorted in alphabetical order!
        colour=EMBED_COLOR,
        )
        embed.set_author(name="Command List", icon_url=self.bot.user.avatar)

        embed.add_field(name="JUST READ THE COMMAND DESCRIPTIONS!", value="")

        # names on a alphabetical order (A-B-C-D-E-F-G-H-I-J-K-L-M-N-O-P-Q-R-S-T-U-V-W-X-Y-Z)
        # embed.add_field(name="Art", value="submit, suggest\nSubmit a art work when a art contest is going on.\nSuggest a theme for the art contest.", inline=False)
        # embed.add_field(name="Art (admin)", value="recount, remove_suggestion, admin\nCommands to help with running the art contest", inline=False)
        # embed.add_field(name="Balls", value="Dont ask...", inline=False)
        # embed.add_field(name="Help", value="Shows you this menu!", inline=False)
        # embed.add_field(name="Poll", value="Create polls that can be voted with reactions", inline=False)
        # embed.add_field(name="Quote", value="Add a quote in the quotes channel", inline=False)
        # embed.add_field(name="ReactionRole (admin)", value="add, remove, list\nMake the bot give roles on reaction of a message", inline=False)
        # embed.add_field(name="Settings (admin)", value="Bot settings", inline=False)
        # embed.add_field(name="Wmoji", value="add, remove, list\nMake the bot react with a emoji on a word (string)", inline=False)
        # embed.add_field(name="Webtoon", value="get, add\nWebtoon Recommendations", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Help(bot))