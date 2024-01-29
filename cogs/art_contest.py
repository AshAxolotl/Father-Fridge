from discord.ext import commands
import discord
from discord import EventStatus, app_commands, EntityType, PrivacyLevel
import datetime
import json




def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

class ArtContest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # test command
    @app_commands.command(name="test_art", description="im going insane")
    async def test_art(self, interaction: discord.Interaction):
        # Create New Event For Winner Anncouncement
        time_now = discord.utils.utcnow()
        time_day = next_weekday(time_now, 0) #sets the time to coming monday
        time_start = time_day.replace(hour=20, minute=0, second=0)
        time_end = time_day.replace(hour=20, minute=0, second=1)

        await interaction.guild.create_scheduled_event(
            name="Art Contest: winner announcement",
            description="vote on winner ig",
            start_time=time_start,
            end_time=time_end,
            privacy_level=PrivacyLevel.guild_only,
            entity_type=EntityType.external,
            location="TEST TES TEST"
        )
        
        await interaction.response.send_message("succes?", ephemeral=True)

    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event):
        # print("CREATE " + str(event))
        pass
    
    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event):
        # print("DELETE " + str(event))
        pass
    
    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        # Checks if the creator is the bot
        if before.creator == self.bot.user:
            print("----")

            announcements_channel = self.bot.get_channel(self.bot.data["artContestAnnouncementsChannel"]) #maybe move this line?
            event_theme_announcement_name = "Art Contest: theme anncouncement"
            event_winner_announcement_name = "Art Contest: winner announcement"
            theme = self.bot.data["artContestTheme"]
            event_art_contest_name = f"Art Contest: {theme}"

            # VOTING ON WINNER DONE
            if before.name == event_winner_announcement_name:            
                if before.status == EventStatus.scheduled:
                    if after.status == EventStatus.active:
                        print("VOTING ON WINNER DONE")
                        # Complets the winner  announcement event so it gets removed
                        await after.edit(status=EventStatus.completed)

                        # Send bot Owners DM to place art on the fridge since it cant be automated
                        for user_id in self.bot.OWNER_USERIDS:
                            user = self.bot.get_user(user_id)
                            await user.send("PLACE THE ART ON THE FRIDGE!")

                        await announcements_channel.send(f"John won the art contest! with theme: {theme}")
                        #give winner role code here 

                        
                        ### TIRED ASH NOTES: NEEDS a way of handeling the poll if there no suggestions and when theres no post
                        # New Suggestions Forum Post for theme
                        forum_channel: discord.ForumChannel = before.guild.get_channel(self.bot.data["artContestThemeSuggestionsChannel"])
                        old_thread = forum_channel.get_thread(self.bot.data["artContestThemeSuggestionsThread"])
                        if isinstance(old_thread, discord.Thread): # Checks if the old thread exist 
                            # Making Poll code here
                            messages = [message async for message in old_thread.history(limit=50)]
                            messages = messages[1:-1] # Removes the post name and description from the messages
                            messages.reverse()
                            
                            # Creates theme_idea list with the first 9 entrys of the messages
                            theme_idea: list = []
                            i = 0
                            while i <= min(8, len(messages)):
                                theme_idea.append(messages[i].content)
                                i += 1
                            
                            await old_thread.edit(name=f"OLD Theme Suggestions: {theme}", archived=True, locked=True, pinned=False) # Close old thread for theme suggestions 
                        
                        else:
                            theme_idea: list = ["there were 0 themes suggested (or the bot broke)"]

                        print(theme_idea)

                        await forum_channel.create_thread(name="Theme Suggestions", content="WORDS HERE")
                        self.bot.data["artContestThemeSuggestionsThread"] = forum_channel.last_message_id
                        write_json_data(self.bot.data)
                    
                        time_now = discord.utils.utcnow()
                        time_day = next_weekday(time_now, 1) # sets the time to coming tuesday
                        time_start = time_day.replace(hour=17, minute=0, second=0)
                        time_end = time_day.replace(hour=17, minute=0, second=1)

                        await before.guild.create_scheduled_event(
                            name=event_theme_announcement_name,
                            description="vote on theme ig",
                            start_time=time_start,
                            end_time=time_end,
                            privacy_level=PrivacyLevel.guild_only,
                            entity_type=EntityType.external,
                            location="TEST TES TEST"
                        )


            # VOTING ON THEME DONE
            elif before.name == event_theme_announcement_name:
                if before.status == EventStatus.scheduled:
                    if after.status == EventStatus.active:
                        print("VOTING ON THEME DONE")
                        # Complets the theme announcement event so it gets removed
                        await after.edit(status=EventStatus.completed)

                        await announcements_channel.send("THEME IS TEST!")

                        # Create New Event For Art Contest
                        time_now = discord.utils.utcnow()
                        time_start = time_now.replace(minute=(time_now.minute + 1)) # this needs to be done diffrently since this breaks if the event ends at 59min

                        time_day = next_weekday(time_now, 6) # sets the time to coming sunday
                        time_end = time_day.replace(hour=22, minute=59, second=0)

                        await before.guild.create_scheduled_event(
                            name=f"Art Contest: {theme}",
                            description="make art ig",
                            start_time=time_start,
                            end_time=time_end,
                            privacy_level=PrivacyLevel.guild_only,
                            entity_type=EntityType.external,
                            location="TEST TES TEST"
                        )

                        # code for sumbiting art here?


            # ART CONTEST DONE
            elif before.name == event_art_contest_name:
                if before.status == EventStatus.active:
                    if after.status == EventStatus.completed:
                        print("ART CONTEST DONE")
                        # Create New Event For Winner Anncouncement
                        time_now = discord.utils.utcnow()
                        time_day = next_weekday(time_now, 0) #sets the time to coming monday
                        time_start = time_day.replace(hour=20, minute=0, second=0)
                        time_end = time_day.replace(hour=20, minute=0, second=1)

                        await before.guild.create_scheduled_event(
                            name=event_winner_announcement_name,
                            description="vote on winner ig",
                            start_time=time_start,
                            end_time=time_end,
                            privacy_level=PrivacyLevel.guild_only,
                            entity_type=EntityType.external,
                            location="TEST TES TEST"
                        )

                        # code for making voting for winner here

                    
                    
            
# set up cog
async def setup(bot):
    await bot.add_cog(ArtContest(bot))

# json write (for cogs)
def write_json_data(data):
  data_json = json.dumps(data, indent=4)
  with open("data.json", "w") as file:
    file.write(data_json)


# to do:
# think of way to display current and old theme suggtions