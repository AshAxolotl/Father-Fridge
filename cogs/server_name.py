import discord
from discord import app_commands
from discord.ext import commands
from random import choice
from datetime import timedelta
from zoneinfo import ZoneInfo
from bot_config import TIME_ZONE

@app_commands.guild_only()
class ServerName(commands.GroupCog, name="server_name"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    # add
    @app_commands.command(name="suggest", description="Suggest a server name")
    async def suggest(self, interaction: discord.Interaction, text: str):
        await self.bot.pool.execute(f"""
            INSERT INTO server_name_suggestions
            (guild_id, user_id, name_suggestion)
            VALUES ({interaction.guild_id}, {interaction.user.id}, $1)
            ON CONFLICT (guild_id, user_id) DO
                UPDATE SET name_suggestion = EXCLUDED.name_suggestion;
        """, text)
        await interaction.response.send_message(f"Your suggestion for this guild has been set to {text}", ephemeral=True)

    # remove
    @app_commands.command(name="remove", description="Remove a suggestion")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove(self, interaction: discord.Interaction, suggestion: str):
        await self.bot.pool.execute(f"DELETE FROM server_name_suggestions WHERE name_suggestion = $1 AND guild_id = {interaction.guild_id}", suggestion)
        await interaction.response.send_message(f"Tried to remove all suggestions with the text: {suggestion}", ephemeral=True)

    # list
    @app_commands.command(name="list", description="List all suggestions for this guild")
    async def list(self, interaction: discord.Interaction):
        text = "list of server name suggestions:\n"
        
        records = await self.bot.pool.fetch(f"""
        SELECT user_id, name_suggestion FROM server_name_suggestions
        WHERE guild_id = {interaction.guild_id};
        """, )

        for record in records:
            name = discord.utils.get(interaction.guild.members, id=record['user_id'])
            text += f"{name}: {record['name_suggestion']}\n"
        
        await interaction.response.send_message(text, ephemeral=True)



    # create event    
    @app_commands.command(name="event", description="Creates the scheduled event")
    @app_commands.checks.has_permissions(administrator=True)
    async def event(self, interaction: discord.Interaction):
        # New scheduled event for server rename                 
        time_now = discord.utils.utcnow().astimezone(ZoneInfo(TIME_ZONE))
        time_start = time_now.replace(hour=23, minute=59, second=0)
        time_end = time_now.replace(hour=23, minute=59, second=1)

        await interaction.guild.create_scheduled_event(
        name="Daily Server Rename",
        description="Suggest names by using /server_name suggest",
        start_time=time_start,
        end_time=time_end,
        privacy_level=discord.PrivacyLevel.guild_only,
        entity_type=discord.EntityType.external,
        location="Suggest names by using /server_name suggest"
        )
        await interaction.response.send_message("Created scheduled event for name change", ephemeral=True)

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        if before.creator == self.bot.user:
            if before.name == "Daily Server Rename":            
                if before.status == discord.EventStatus.scheduled:
                    if after.status == discord.EventStatus.active:
                        await after.edit(status=discord.EventStatus.completed)
                        # New scheduled event for server rename                 
                        time_now = discord.utils.utcnow().astimezone(ZoneInfo(TIME_ZONE)) + timedelta(days=1)
                        time_start = time_now.replace(hour=23, minute=59, second=0)
                        time_end = time_now.replace(hour=23, minute=59, second=1)

                        await before.guild.create_scheduled_event(
                        name="Daily Server Rename",
                        description="Suggest names by using /server_name suggest",
                        start_time=time_start,
                        end_time=time_end,
                        privacy_level=discord.PrivacyLevel.guild_only,
                        entity_type=discord.EntityType.external,
                        location="Suggest names by using /server_name suggest"
                        )

                        records = await self.bot.pool.fetch(f"""
                        SELECT name_suggestion FROM server_name_suggestions
                        WHERE guild_id = {before.guild_id} AND name_suggestion != $1;
                        """, before.guild.name)
                    
                        await before.guild.edit(reason="Daily Rename", name="There where no valid suggestions" if len(records) == 0 else choice(records)['name_suggestion'])

                        
                        


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ServerName(bot))