from discord.ext import commands
import discord
from discord import EventStatus, app_commands, EntityType, PrivacyLevel
import datetime
from random import choice
import google_api_stuff as google_api_stuff
from googleapiclient.errors import HttpError
from typing import Optional, Literal
from bot_config import NO_PERMS_MESSAGE
import asyncpg


# function for setting a datetime to a spesfic day next week
def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

# create a scheduled event
async def create_scheduled_event(guild: discord.Guild, name: str, time_start: datetime.datetime, time_end: datetime.datetime, description="", locaction=""):
    await guild.create_scheduled_event(
        name=name,
        description=description,
        start_time=time_start,
        end_time=time_end,
        privacy_level=PrivacyLevel.guild_only,
        entity_type=EntityType.external,
        location=locaction
    )

async def send_theme_suggestions_msg(guild_id: int, suggestions_channel: int) -> int:
    # Creates a new message for showing suggested themes
    suggestion_embed = discord.Embed(title="Use /art suggest <theme> in another channel to suggested a theme!", description="Current Suggestions:", colour=discord.Colour.dark_gold())
    suggestion_embed.set_author(name="Theme Suggestions")
    suggestion_embed.add_field(name="PLACE HOLDER", value=" -Father Fridge", inline=False)
    
    suggestion_message = await suggestions_channel.send(embed=suggestion_embed, silent=True)
    return suggestion_message.id


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

    # start new
    @app_commands.command(name="start_new", description="setup the art contest")
    @app_commands.checks.has_permissions(administrator=True)
    async def start_new(self, interaction: discord.Interaction):
        records = await self.bot.pool.fetch(f"""
        SELECT art_contest_announcements_channel_id, art_contest_theme_suggestion_channel_id FROM settings
        WHERE guild_id = {interaction.guild_id};
        """, )

        # Get channels
        suggestions_channel: discord.TextChannel = interaction.guild.get_channel()

        suggestions_message_id = send_theme_suggestions_msg(interaction.guild_id, 0)

        await self.bot.pool.execute(f"""
        UPDATE settings
        SET art_contest_theme_suggestions_message_id = {suggestions_message_id}
        WHERE guild_id = {interaction.guild_id}
        """)

        # New scheduled event for theme annoucement                   
        time_now = discord.utils.utcnow()
        time_day = next_weekday(time_now, 1) # sets the time to coming tuesday
        time_start = time_day.replace(hour=17, minute=0, second=0)
        time_end = time_day.replace(hour=17, minute=0, second=1)

        await create_scheduled_event(
            guild=interaction.guild,
            name="Art Contest: winner announcement",
            description="Vote on the theme for the next art contest!",
            start_time=time_start,
            end_time=time_end,
            location=f"https://discord.com/channels/{interaction.guild_id}/{announcements_channel}"
        )
        
        await interaction.response.send_message(f"testing 123 TODO", ephemeral=True)
    
    @start_new.error
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

                        # suggestions_channel: discord.TextChannel = before.guild.get_channel(self.bot.data["artContestThemeSuggestionsChannel"])
                        # announcements_channel: discord.TextChannel = before.guild.get_channel(self.bot.data["artContestAnnouncementsChannel"])

                        # # Get winner
                        # winner_embed_info = await get_contest_winner(self)
                            
                        # winner_embed = discord.Embed(title="", description=winner_embed_info["text"], colour=discord.Colour.dark_gold())
                        # winner_embed.set_author(name=f"Voting Results: {theme}", url=self.bot.data["artContestResponderUri"])
                        # winner_embed.set_image(url=winner_embed_info["image_url"])
                        # winner_embed.set_footer(text="winner(s) shall be put on the fridge in 3-5 business day")
                        
                        # await announcements_channel.send(f"<@&{self.bot.data['artContestRole']}>", embed=winner_embed)


                        # # Create theme poll
                        # poll_options_text: str = ""
                        # number: int = 0
                        # for key in self.bot.data["artContestThemeSuggestions"]:
                        #     number += 1
                        #     emoji = str(number) + "\ufe0f\u20e3" # number emojis 1️⃣
                        #     poll_option = self.bot.data["artContestThemeSuggestions"][key]
                        #     poll_options_text += f"{emoji} {poll_option}\n"
                        
                        # poll_embed = discord.Embed(title="", description=poll_options_text, colour=discord.Colour.dark_gold())
                        # poll_embed.set_author(name="Vote for the contest theme!")

                        # poll_message = await announcements_channel.send(embed=poll_embed, silent=True)
                        # self.bot.data["artContestThemePollMessage"] = poll_message.id
                        
                        # # Adds the emojis to the theme poll so it can be voted on
                        # for i in range(len(self.bot.data["artContestThemeSuggestions"])):
                        #     emoji = str(i + 1) + "\ufe0f\u20e3"
                        #     await poll_message.add_reaction(emoji)

                        # # Resets the list of reactions that is being kept to make sure people can only vote 1 thing
                        # self.bot.data["artContestThemePollReactions"] = {}

                        
                        # # Creates a new message for showing suggested themes
                        # suggestion_embed = discord.Embed(title="Use /art suggest <theme> in another channel to suggested a theme!", description="Current Suggestions:", colour=discord.Colour.dark_gold())
                        # suggestion_embed.set_author(name="Theme Suggestions")
                        # suggestion_embed.add_field(name="PLACE HOLDER", value=" -Father Fridge", inline=False)
                        
                        # suggestion_message = await suggestions_channel.send(embed=suggestion_embed, silent=True)

                        # self.bot.data["artContestThemeSuggestionsMessage"] = suggestion_message.id
                        # self.bot.data["artContestThemeSuggestions"] = {str(self.bot.user.id): "PLACE HOLDER"} # clears the theme suggestions

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

                        # # Get channel
                        # announcements_channel: discord.TextChannel = before.guild.get_channel(self.bot.data["artContestAnnouncementsChannel"])
                        # submission_channel_id = self.bot.data["artContestSubmissionsChannel"]

                        # # Gets the winning theme from the poll
                        # poll_message: discord.Message = await announcements_channel.fetch_message(self.bot.data["artContestThemePollMessage"])
                        # reactions = sorted(poll_message.reactions, key=lambda reaction: reaction.count, reverse=True) # sorts the reactions based on count from high to low
                        # highest_count = reactions[0].count
                        # winning_emojis = [] 
                        # # makes a list of the most reacted emojis
                        # for reaction in reactions:
                        #     if reaction.count == highest_count:
                        #         winning_emojis.append(reaction.emoji)

                        # # gets the winning theme's name and handels more then 1 winner
                        # embed = poll_message.embeds[0]
                        # suggested_themes = embed.description.split("\n")
                        # winning_emoji = choice(winning_emojis) # randomly selects a emoji from the winning emojis list
                        # for suggested_theme in suggested_themes:
                        #     if suggested_theme.startswith(winning_emoji):
                        #         winning_theme = suggested_theme.replace(winning_emoji + " ", "") # removes the emoji from the start of the text

                        # await announcements_channel.send(f"<@&{self.bot.data['artContestRole']}> Theme \"{winning_theme}\" won the poll. Good luck with your art!", reference=poll_message)

                        # self.bot.data["artContestTheme"] = winning_theme

                        # # Resets the submissions
                        # self.bot.data["artContestActive"] = True
                        # self.bot.data["artContestSubmissions"] = {}

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
                        # create_result = google_api_stuff.create_form(self.bot.data)

                        # await announce_winner_form(self, create_result)

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
