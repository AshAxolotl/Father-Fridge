import json
import discord
from discord import app_commands, ChannelType, ui
from discord.ext import commands
from typing import Any, List, Union
from bot_config import NO_PERMS_MESSAGE

# BASE MENU seen when using /settings
baseMenuEmbed = discord.Embed(
        colour=discord.Colour.dark_gold(),
        title="Settings: Start Menu",
        description="SETTINGS",
)


class BaseMenuView(ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction
        

        async def on_timeout(self) -> None:
            await self.disable_all_items()

    # Join Role
    @ui.button(label="Join Settings", style=discord.ButtonStyle.blurple)
    async def join_role(self, interaction: discord.Interaction, button: ui.Button):
        role_id = await interaction.client.pool.fetchval(f"SELECT join_role_id FROM settings WHERE guild_id = '{interaction.guild_id}'")
        view = JoinSettingsView(dropdown=[JoinRoleDropdown(self.interaction, role_id)])
        embed = discord.Embed(colour=discord.Colour.dark_gold(), title="Settings: Join Role", description="Set the role that users should get when they join the guild.")
        await interaction.response.edit_message(view=view, embed=embed)
        self.stop()

    #Quote Channel
    @ui.button(label="Quote Channel", style=discord.ButtonStyle.blurple)
    async def quote_channel(self, interaction: discord.Interaction, button: ui.Button):
        quote_channel_id = await interaction.client.pool.fetchval(f"SELECT quote_channel_id FROM settings WHERE guild_id = '{interaction.guild_id}'")
        view = DropdownView(dropdown=[QuoteChannelDropdown(self.interaction, quote_channel_id)])
        embed = discord.Embed(colour=discord.Colour.dark_gold(), title="Settings: Quote Channel", description="Set the channel where quotes will go")
        await interaction.response.edit_message(view=view, embed=embed)
        self.stop()

    #Art Contest
    @ui.button(label="Art Contest", style=discord.ButtonStyle.blurple)
    async def art_contest(self, interaction: discord.Interaction, button: ui.Button):
        records = await interaction.client.pool.fetchrow(f"""
        SELECT art_contest_announcements_channel_id, art_contest_theme_suggestion_channel_id, art_contest_submissions_channel_id, art_contest_role_id FROM settings
        WHERE guild_id = {interaction.guild_id};
        """, )

        view = DropdownView(dropdown=[ArtContestAnnouncementsDropdown(self.interaction, records["art_contest_announcements_channel_id"]), 
                                      ArtContestThemeSuggestionsDropdown(self.interaction, records["art_contest_theme_suggestion_channel_id"]), 
                                      ArtContestSubmissionsDropdown(self.interaction, records["art_contest_submissions_channel_id"]), 
                                      ArtContestRoleDropdown(self.interaction, records["art_contest_role_id"])])
        embed = discord.Embed(colour=discord.Colour.dark_gold(), title="Settings: Art Contest", description="Settings for art contest channels and roles")
        await interaction.response.edit_message(view=view, embed=embed)
        self.stop()


        
## VIEWS
# base drop down view
class DropdownView(ui.View):
    def __init__(self, dropdown):
        super().__init__()
        # Adds the dropdown to our view object.
        for i in dropdown:
            self.add_item(i)
    
    @ui.button(label="Back", style=discord.ButtonStyle.gray, row=4)
    async def back_button(self, interaction: discord.Interaction, button: ui.button):
        view = BaseMenuView(interaction)
        await interaction.response.edit_message(view=view, embed=baseMenuEmbed)

# Join settings view
class JoinSettingsView(ui.View):
    def __init__(self, dropdown):
        super().__init__()
        # Adds the dropdown to our view object.
        for i in dropdown:
            self.add_item(i)
    
    @ui.button(label="Back", style=discord.ButtonStyle.gray, row=1)
    async def back_button(self, interaction: discord.Interaction, button: ui.button):
        view = BaseMenuView(interaction)
        await interaction.response.edit_message(view=view, embed=baseMenuEmbed)


## BUTTON
# TODO add the back button here as a class?


## DROPDOWNS
# Join Role Dropdown
class JoinRoleDropdown(ui.RoleSelect):
    def __init__(self, interaction: discord.Interaction, role_id):
        role = interaction.guild.get_role(role_id)
        super().__init__(placeholder=f"Join Role: {role}", min_values=1, max_values=1)
        
    async def callback(self, interaction: discord.Interaction):
        roles: List[discord.Role] = self.values
        selected_roles = [
            role
            for role in roles
        ]
        await interaction.client.pool.execute(f"""
            UPDATE settings
            SET join_role_id = {selected_roles[0].id}
            WHERE guild_id = {interaction.guild_id}
        """)
        await interaction.response.send_message(f"Successfully set join role to <@&{selected_roles[0].id}>", ephemeral=True)


# Quote Channel Dropdown
class QuoteChannelDropdown(ui.ChannelSelect):
    def __init__(self, interaction: discord.Interaction, quote_channel_id):
        channel = interaction.guild.get_channel(quote_channel_id)
        super().__init__(placeholder=f"Quote Channel: {channel}", min_values=1, max_values=1, channel_types=[ChannelType.text])
        
    async def callback(self, interaction: discord.Interaction):
        channels: List[Union[app_commands.AppCommandChannel, app_commands.AppCommandThread]] = self.values
        selected_channels = [
            channel
            for channel in channels
        ]

        await interaction.client.pool.execute(f"""
            UPDATE settings
            SET quote_channel_id = {selected_channels[0].id}
            WHERE guild_id = {interaction.guild_id}
        """)
        await interaction.response.send_message(f"Successfully set quote channel to https://discord.com/channels/{interaction.guild_id}/{selected_channels[0].id}", ephemeral=True, suppress_embeds=True)

# Art Contest Announcements Channel Dropdown
class ArtContestAnnouncementsDropdown(ui.ChannelSelect):
    def __init__(self, interaction: discord.Interaction, art_contest_announcements_channel_id):
        channel = interaction.guild.get_channel(art_contest_announcements_channel_id)
        super().__init__(placeholder=f"Announcements channel: {channel}", min_values=1, max_values=1, channel_types=[ChannelType.text])
        
    async def callback(self, interaction: discord.Interaction):
        channels: List[Union[app_commands.AppCommandChannel, app_commands.AppCommandThread]] = self.values
        selected_channels = [
            channel
            for channel in channels
        ]

        await interaction.client.pool.execute(f"""
            UPDATE settings
            SET art_contest_announcements_channel_id = {selected_channels[0].id}
            WHERE guild_id = {interaction.guild_id}
        """)
        await interaction.response.send_message(f"Successfully set the art contest announcements channel to https://discord.com/channels/{interaction.guild_id}/{selected_channels[0].id}", ephemeral=True, suppress_embeds=True)

# Art Contest Theme Suggestions Channel Dropdown
class ArtContestThemeSuggestionsDropdown(ui.ChannelSelect):
    def __init__(self, interaction: discord.Interaction, art_contest_theme_suggestion_channel_id):
        channel = interaction.guild.get_channel(art_contest_theme_suggestion_channel_id)
        super().__init__(placeholder=f"Theme Suggestions channel: {channel}", min_values=1, max_values=1, channel_types=[ChannelType.text])
        
    async def callback(self, interaction: discord.Interaction):
        channels: List[Union[app_commands.AppCommandChannel, app_commands.AppCommandThread]] = self.values
        selected_channels = [
            channel
            for channel in channels
        ]

        await interaction.client.pool.execute(f"""
            UPDATE settings
            SET art_contest_theme_suggestion_channel_id = {selected_channels[0].id}
            WHERE guild_id = {interaction.guild_id}
        """)
        await interaction.response.send_message(f"Successfully set the art contest theme suggestions channel to https://discord.com/channels/{interaction.guild_id}/{selected_channels[0].id}", ephemeral=True, suppress_embeds=True)

# Art Contest Submission Channel Dropdown
class ArtContestSubmissionsDropdown(ui.ChannelSelect):
    def __init__(self, interaction: discord.Interaction, art_contest_submissions_channel_id):
        channel = interaction.guild.get_channel(art_contest_submissions_channel_id)
        super().__init__(placeholder=f"Submissions channel: {channel}", min_values=1, max_values=1, channel_types=[ChannelType.forum])
        
    async def callback(self, interaction: discord.Interaction):
        channels: List[Union[app_commands.AppCommandChannel, app_commands.AppCommandThread]] = self.values
        selected_channels = [
            channel
            for channel in channels
        ]

        await interaction.client.pool.execute(f"""
            UPDATE settings
            SET art_contest_submissions_channel_id = {selected_channels[0].id}
            WHERE guild_id = {interaction.guild_id}
        """)
        await interaction.response.send_message(f"Successfully set the art contest Submissions channel to https://discord.com/channels/{interaction.guild_id}/{selected_channels[0].id}", ephemeral=True, suppress_embeds=True)

# Art Contest Role Dropdown
class ArtContestRoleDropdown(ui.RoleSelect):
    def __init__(self, interaction: discord.Interaction, art_contest_role_id):
        role = interaction.guild.get_role(art_contest_role_id)
        super().__init__(placeholder=f"Role: {role}", min_values=1, max_values=1)
        
    async def callback(self, interaction: discord.Interaction):
        roles: List[discord.Role] = self.values
        selected_roles = [
            role
            for role in roles
        ]
        await interaction.client.pool.execute(f"""
            UPDATE settings
            SET art_contest_role_id = {selected_roles[0].id}
            WHERE guild_id = {interaction.guild_id}
        """)
        await interaction.response.send_message(f"Successfully set the art contest role to <@&{selected_roles[0].id}>", ephemeral=True)



## COMMANDS
# /settings
class Settings(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot

    @app_commands.command(name="settings", description="bot settings")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def settings(self, interaction:discord.Interaction):
        # embed

        view = BaseMenuView(interaction)

        
        await interaction.response.send_message(embed=baseMenuEmbed, view=view, ephemeral=True)
    
    # error for if user of command doesnt have the perms
    @settings.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True)



# loading the cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Settings(bot))


# json write (for cogs)
def write_json_data(data):
  data_json = json.dumps(data, indent=4)
  with open("data.json", "w") as file:
    file.write(data_json)
