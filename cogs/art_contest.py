from discord.ext import commands
import discord
from discord import EventStatus, app_commands, EntityType, PrivacyLevel
import datetime
from random import choice
import google_api_stuff as google_api_stuff
from googleapiclient.errors import HttpError
from typing import Optional, Literal
from bot_config import NO_PERMS_MESSAGE


# function for setting a datetime to a spesfic day next week
def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

# create a scheduled event
async def create_scheduled_event(guild: discord.guild, name: str, time_start: datetime.datetime, time_end: datetime.datetime, description="", locaction=""):
    await guild.create_scheduled_event(
        name=name,
        description=description,
        start_time=time_start,
        end_time=time_end,
        privacy_level=PrivacyLevel.guild_only,
        entity_type=EntityType.external,
        location=locaction
    )


class ArtContest(commands.GroupCog, name="art"):
    def __init__(self, bot):
        self.bot = bot
        self.event_theme_announcement_name = "Art Contest: theme announcement"
        self.event_winner_announcement_name = "Art Contest: winner announcement"
        self.event_art_contest_name = "Art Contest: "


    ## ADMIN COMMANDS
    # create event command (WIP THIS CODE IS SHIT AND SHOULD BE REPLACED)
    @app_commands.command(name="create_event", description="make a scheduled event (ADMIN ONLY)")
    @app_commands.checks.has_permissions(administrator=True)
    async def create_event(self, interaction: discord.Interaction, event: Literal["winner", "theme", "active"]):
        if event == "theme":
            # New scheduled event for theme annoucement
            time = next_weekday(discord.utils.utcnow(), 1) # sets the time to coming tuesday
            await create_scheduled_event(
                guild=interaction.guild,
                name=self.event_theme_announcement_name,
                time_start=time.replace(hour=17, minute=0, second=0),
                time_end=time.replace(hour=17, minute=0, second=1)
            )
        
        elif event == "active":
            # Create New Event For Art Contest
            time = discord.utils.utcnow()
            await create_scheduled_event(
                guild=interaction.guild,
                name=f"{self.event_art_contest_name}THEME HERE",
                time_start=(time + datetime.timedelta(seconds=5)),
                time_end=next_weekday(time, 6).replace(hour=22, minute=59, second=0)
            )
            

        elif event == "winner":
            # Create New Event For Winner Announcement
            time = next_weekday(discord.utils.utcnow(), 0) # Sets the time to coming monday
            await create_scheduled_event(
                guild=interaction.guild,
                name=self.event_winner_announcement_name,
                time_start=time.replace(hour=20, minute=0, second=0),
                time_end=time.replace(hour=20, minute=0, second=1)
            )
        
        await interaction.response.send_message("Event has been made", ephemeral=True)

    @create_event.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True)

    
    ## LISTENERS
    # Scheduled Event Changes 
    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        # Checks if the creator is the bot
        if before.creator == self.bot.user:
            

            theme = "THEME HERE"

            # VOTING ON WINNER DONE
            if before.name == self.event_winner_announcement_name:            
                if before.status == EventStatus.scheduled:
                    if after.status == EventStatus.active:
                        # Complets the winner  announcement event so it gets removed
                        await after.edit(status=EventStatus.completed)

                        # New scheduled event for theme annoucement
                        time = next_weekday(discord.utils.utcnow(), 1) # sets the time to coming tuesday
                        await create_scheduled_event(
                            guild=after.guild,
                            name=self.event_theme_announcement_name,
                            time_start=time.replace(hour=17, minute=0, second=0),
                            time_end=time.replace(hour=17, minute=0, second=1)
                        )



            # VOTING ON THEME DONE
            elif before.name == self.event_theme_announcement_name:
                if before.status == EventStatus.scheduled:
                    if after.status == EventStatus.active:
                        # Complets the theme announcement event so it gets removed
                        await after.edit(status=EventStatus.completed)

                        winning_theme = "THEME HERE"

                        # Create New Event For Art Contest
                        time = discord.utils.utcnow()
                        await create_scheduled_event(
                            guild=after.guild,
                            name=f"{self.event_art_contest_name}{winning_theme}",
                            time_start=(time + datetime.timedelta(seconds=5)),
                            time_end=next_weekday(time, 6).replace(hour=22, minute=59, second=0)
                        )





            # ART CONTEST DONE
            elif before.name == f"{self.event_art_contest_name}{theme}":
                if before.status == EventStatus.active:
                    if after.status == EventStatus.completed:


                        # Create New Event For Winner Announcement
                        time = next_weekday(discord.utils.utcnow(), 0) # Sets the time to coming monday
                        await create_scheduled_event(
                            guild=after.guild,
                            name=self.event_winner_announcement_name,
                            time_start=time.replace(hour=20, minute=0, second=0),
                            time_end=time.replace(hour=20, minute=0, second=1)
                        )



                        


# set up cog
async def setup(bot):
    await bot.add_cog(ArtContest(bot))
