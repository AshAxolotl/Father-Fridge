from discord.ext import commands
import discord
from discord import EventStatus, app_commands, EntityType, PrivacyLevel
import datetime
import json
from random import choice
import google_api_stuff
from googleapiclient.errors import HttpError
from typing import Optional, Literal
from bot_config import NO_PERMS_MESSAGE

# function for setting a datetime to a spesfic day next week
def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)



class ArtContest(commands.GroupCog, name="art"):
    def __init__(self, bot):
        self.bot = bot


    ## COMMANDS
    # Art Test command
    @app_commands.command(name="art_test", description="axe asked for this shit")
    async def art_test(self, interaction: discord.Interaction):
        time = self.next_weekday(discord.utils.utcnow(), 2)
        await interaction.response.send_message(f"test {time}")


    ## LISTENERS
    # Scheduled Event Changes 
    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        # Checks if the creator is the bot
        if before.creator == self.bot.user:
            event_theme_announcement_name = "Art Contest: theme announcement"
            event_winner_announcement_name = "Art Contest: winner announcement"
            theme = self.bot.data["artContestTheme"]
            event_art_contest_name = f"Art Contest: {theme}"

            # VOTING ON WINNER DONE
            if before.name == event_winner_announcement_name:            
                if before.status == EventStatus.scheduled:
                    if after.status == EventStatus.active:
                        # Complets the winner  announcement event so it gets removed
                        await after.edit(status=EventStatus.completed)

                        # New scheduled event for theme annoucement                   
                        time_now = discord.utils.utcnow()
                        time_day = next_weekday(time_now, 1) # sets the time to coming tuesday
                        time_start = time_day.replace(hour=17, minute=0, second=0)
                        time_end = time_day.replace(hour=17, minute=0, second=1)

                        await before.guild.create_scheduled_event(
                            name=event_theme_announcement_name,
                            description="Vote on the theme for the next art contest!",
                            start_time=time_start,
                            end_time=time_end,
                            privacy_level=PrivacyLevel.guild_only,
                            entity_type=EntityType.external,
                            location="" #f"https://discord.com/channels/{before.guild_id}/{announcements_channel.id}"
                        )


            # VOTING ON THEME DONE
            elif before.name == event_theme_announcement_name:
                if before.status == EventStatus.scheduled:
                    if after.status == EventStatus.active:
                        # Complets the theme announcement event so it gets removed
                        await after.edit(status=EventStatus.completed)

                        winning_theme = ""

                        # Create New Event For Art Contest
                        time_now = discord.utils.utcnow()
                        time_start = time_now + datetime.timedelta(seconds=10)

                        time_day = next_weekday(time_now, 6) # sets the time to coming sunday
                        time_end = time_day.replace(hour=22, minute=59, second=0)

                        await before.guild.create_scheduled_event(
                            name=f"Art Contest: {winning_theme}",
                            description="Make art using the theme!\nFor more information check the info channel!",
                            start_time=time_start,
                            end_time=time_end,
                            privacy_level=PrivacyLevel.guild_only,
                            entity_type=EntityType.external,
                            location="" #f"https://discord.com/channels/{before.guild_id}/{submission_channel_id}"
                        )


            # ART CONTEST DONE
            elif before.name == event_art_contest_name:
                if before.status == EventStatus.active:
                    if after.status == EventStatus.completed:
                        

                        # Create New Event For Winner Announcement
                        time_now = discord.utils.utcnow()
                        time_day = next_weekday(time_now, 0) #sets the time to coming monday
                        time_start = time_day.replace(hour=20, minute=0, second=0)
                        time_end = time_day.replace(hour=20, minute=0, second=1)

                        await before.guild.create_scheduled_event(
                            name=event_winner_announcement_name,
                            description="Vote on the art contest winner!",
                            start_time=time_start,
                            end_time=time_end,
                            privacy_level=PrivacyLevel.guild_only,
                            entity_type=EntityType.external,
                            location="Checks art contest announcements!"
                        )



# set up cog
async def setup(bot):
    await bot.add_cog(ArtContest(bot))