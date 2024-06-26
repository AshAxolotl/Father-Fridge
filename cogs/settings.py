from datetime import datetime
import discord
from discord import app_commands, ChannelType, ui
from discord.ext import commands
from typing import Any, List, Union
from bot_config import EMBED_COLOR



## COMMANDS
# /settings
class Settings(commands.Cog):
    def __init__(self, bot: commands.bot) -> None:
        self.bot = bot

    @app_commands.command(name="settings", description="Bot settings for this guild")
    @app_commands.guild_only()
    @app_commands.checks.has_permissions(administrator=True)
    async def settings(self, interaction:discord.Interaction):
        await interaction.response.send_message(embed=MainMenuEmbed(), view=MainMenuView(interaction), ephemeral=True)


# Back Button
class BackButton(ui.Button):
    def __init__(self):
        super().__init__(label="Back", style=discord.ButtonStyle.gray, row=4)

    
    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=MainMenuView(interaction), embed=MainMenuEmbed())

# Main Menu Embed
class MainMenuEmbed(discord.Embed):
    def __init__(self):
        super().__init__(colour=EMBED_COLOR, title="Settings: Start Menu", description="SETTINGS")
    

# Main Menu View
class MainMenuView(ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__()
        self.interaction = interaction
        

        async def on_timeout(self) -> None:
            await self.disable_all_items()

    # Join Role
    @ui.button(label="Join Settings", style=discord.ButtonStyle.blurple)
    async def join_role(self, interaction: discord.Interaction, button: ui.Button):
        role_id = await interaction.client.pool.fetchval(f"SELECT join_role_id FROM settings WHERE guild_id = '{interaction.guild_id}'")
        view = DropdownView(dropdown=[JoinRoleDropdown(self.interaction, role_id)])
        embed = discord.Embed(colour=EMBED_COLOR, title="Settings: Join Role", description="Set the role that users should get when they join the guild.")
        await interaction.response.edit_message(view=view, embed=embed)
        self.stop()

    #Quote Channel
    @ui.button(label="Quote Channel", style=discord.ButtonStyle.blurple)
    async def quote_channel(self, interaction: discord.Interaction, button: ui.Button):
        quote_channel_id = await interaction.client.pool.fetchval(f"SELECT quote_channel_id FROM settings WHERE guild_id = '{interaction.guild_id}'")
        view = DropdownView(dropdown=[QuoteChannelDropdown(self.interaction, quote_channel_id)])
        embed = discord.Embed(colour=EMBED_COLOR, title="Settings: Quote Channel", description="Set the channel where quotes will go")
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
        embed = discord.Embed(colour=EMBED_COLOR, title="Settings: Art Contest", description="Settings for art contest channels and roles")
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

        self.add_item(BackButton())


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



# loading the cog
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Settings(bot))
