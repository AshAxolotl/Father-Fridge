import json
import discord
from discord import app_commands, ChannelType
from discord.ext import commands
from discord.ui import ChannelSelect
from typing import Any, List, Union

# BASE MENU seen when using /settings
baseMenuEmbed = discord.Embed(
        colour=discord.Colour.dark_gold(),
        title="Settings: Start Menu",
        description="SETTINGS",
)

class BaseMenuView(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction
        

        async def on_timeout(self) -> None:
            print("timed out...")
            await self.disable_all_items()

    # Join Role
    @discord.ui.button(label="Join Role", style=discord.ButtonStyle.blurple)
    async def join_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = DropdownView(dropdown=JoinRoleDropdown(self.interaction))
        embed = discord.Embed(colour=discord.Colour.dark_gold(), title="Settings: Join Role", description="Set the role that users should get when they join the guild.")
        await interaction.response.edit_message(view=view, embed=embed)
        self.stop()

    #Quote Channel
    @discord.ui.button(label="Quote Channel", style=discord.ButtonStyle.blurple)
    async def join_role2(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = DropdownView(dropdown=QuoteChannelDropdown(self.interaction))
        embed = discord.Embed(colour=discord.Colour.dark_gold(), title="Settings: Quote Channel", description="Set the channel where quotes will go")
        await interaction.response.edit_message(view=view, embed=embed)
        self.stop()

        
# base drop down
class DropdownView(discord.ui.View):
    def __init__(self, dropdown):
        super().__init__()
        # Adds the dropdown to our view object.
        self.add_item(dropdown)
    
    @discord.ui.button(label="Back", style=discord.ButtonStyle.gray, row=4)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.button):
        view = BaseMenuView(interaction)
        await interaction.response.edit_message(view=view, embed=baseMenuEmbed)




# Join Role Dropdown
class JoinRoleDropdown(discord.ui.RoleSelect):
    def __init__(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(interaction.client.data["joinRole"])
        super().__init__(placeholder=f"Join Role: {role}", min_values=1, max_values=1)
        
    async def callback(self, interaction: discord.Interaction):
        print("JOINROLE")
        roles: List[discord.Role] = self.values
        selected_roles = [
            role
            for role in roles
        ]
        interaction.client.data["joinRole"] = selected_roles[0].id
        write_json_data(interaction.client.data)
        await interaction.response.send_message(f"Successfully set join role to {selected_roles[0]}", ephemeral=True)


# Quote Channel Dropdown
class QuoteChannelDropdown(discord.ui.ChannelSelect):
    def __init__(self, interaction: discord.Interaction):
        channel = interaction.guild.get_channel(interaction.client.data["quoteChannel"])
        super().__init__(placeholder=f"Quote Channel: {channel}", min_values=1, max_values=1, channel_types=[ChannelType.text])
        
    async def callback(self, interaction: discord.Interaction):
        channels: List[Union[app_commands.AppCommandChannel, app_commands.AppCommandThread]] = self.values
        selected_channels = [
            channel
            for channel in channels
        ]
        print(selected_channels)
        print(selected_channels[0].id)
        interaction.client.data["quoteChannel"] = selected_channels[0].id
        write_json_data(interaction.client.data)
        await interaction.response.send_message(f"Successfully set quote channel to {selected_channels[0].name}", ephemeral=True)




# the command
class Settings(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot

    @app_commands.command(name="settings", description="bot settings")
    @app_commands.checks.has_permissions(administrator=True)
    async def settings(self, interaction:discord.Interaction):
        # embed

        view = BaseMenuView(interaction)

        
        await interaction.response.send_message(embed=baseMenuEmbed, view=view, ephemeral=True)
    
    # error for if user of command doesnt have the perms
    @settings.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have the perms for this (L bozo go cry about it)!", ephemeral=True)



# loading the cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Settings(bot))


# json write (for cogs)
def write_json_data(data):
  data_json = json.dumps(data)
  with open("data.json", "w") as file:
    file.write(data_json)
