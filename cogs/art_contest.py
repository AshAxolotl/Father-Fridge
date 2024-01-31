from discord.ext import commands
import discord
from discord import EventStatus, app_commands, EntityType, PrivacyLevel
import datetime
import json
from random import choice




def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

class ArtContest(commands.GroupCog, name="art"):
    def __init__(self, bot):
        self.bot = bot

    # test command
    @app_commands.command(name="test", description="im going insane")
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
        
        await interaction.response.send_message(f"succes?", ephemeral=True)
    
    # Suggest Theme Command
    @app_commands.command(name="suggest_theme", description="suggest a theme!")
    async def suggest_theme(self, interaction: discord.Interaction, theme: app_commands.Range[str, 1, 50]):
        # checks there arent already more suggestions then the cap
        if len(self.bot.data["artContestThemeSuggestions"]) < 9:
            self.bot.data["artContestThemeSuggestions"][str(interaction.user.id)] = theme
            # delets the place holder theme suggestion
            # if str(self.bot.user.id) in self.bot.data["artContestThemeSuggestions"]:
            #     del self.bot.data["artContestThemeSuggestions"][str(self.bot.user.id)] 
            
            channel: discord.TextChannel = interaction.guild.get_channel(self.bot.data["artContestThemeSuggestionsChannel"])
            message: discord.Message  = await channel.fetch_message(self.bot.data["artContestThemeSuggestionsMessage"])
            embed: discord.Embed = message.embeds[0] # gets the embed that needs to be edited

            # clears all the fields to make sure that 1 person cant suggest more
            embed.clear_fields()
            for key in self.bot.data["artContestThemeSuggestions"]:
                username = self.bot.get_user(int(key)).name
                embed.add_field(name=self.bot.data["artContestThemeSuggestions"][key], value=username, inline=False)

            await message.edit(embed=embed)
            await interaction.response.send_message(f"{theme} is added to the suggestions", ephemeral=True)
            write_json_data(self.bot.data)
        else:
            await interaction.response.send_message(f"There are already to many suggestions so your suggestions: {theme} wasn't added (conntact ash about this)")


    # WIP make sure player can only vote for 1 theme (THIS ISNT GREAT SINCE ITS NOT SPAM PROOF MIGHT HAVE TO REPLACE IT WITH bUTTONS IDK???)
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # checks if it not the bot
        if payload.user_id != self.bot.user.id:
            if payload.message_id == self.bot.data["artContestThemePollMessage"]:
                messageable: discord.PartialMessageable = self.bot.get_partial_messageable(self.bot.data["artContestAnnouncementsChannel"])
                message: discord.PartialMessage = messageable.get_partial_message(payload.message_id)

                if str(payload.user_id) in self.bot.data["artContestThemePollReactions"]:
                    await message.remove_reaction(self.bot.data["artContestThemePollReactions"][str(payload.user_id)], discord.Object(id=payload.user_id))
            
                self.bot.data["artContestThemePollReactions"][str(payload.user_id)] = payload.emoji.name
                write_json_data(self.bot.data)
    

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        # Checks if the creator is the bot
        if before.creator == self.bot.user:
            announcements_channel: discord.TextChannel = self.bot.get_channel(self.bot.data["artContestAnnouncementsChannel"]) #maybe move this line?
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

                        #WIP get winner of voting code here

                        # Send bot Owners DM to place art on the fridge since it cant be automated
                        for user_id in self.bot.OWNER_USERIDS:
                            user = self.bot.get_user(user_id)
                            await user.send(f"PLACE THE ART ON THE FRIDGE! (for theme: {theme})")

                        await announcements_channel.send(f"John won the art contest! with theme: {theme}")
                        #WIP give winner role code here


                        # Create theme poll
                        poll_options_text: str = ""
                        number: int = 0
                        for key in self.bot.data["artContestThemeSuggestions"]:
                            number += 1
                            emoji = str(number) + "\ufe0f\u20e3" # number emojis 1️⃣
                            poll_option = self.bot.data["artContestThemeSuggestions"][key]
                            poll_options_text += f"{emoji} {poll_option}\n"
                        
                        poll_embed = discord.Embed(title="Vote for a theme!", description=poll_options_text, colour=discord.Colour.dark_gold())
                        poll_message = await announcements_channel.send(embed=poll_embed)
                        self.bot.data["artContestThemePollMessage"] = poll_message.id
                        
                        # Adds the emojis to the theme poll so it can be voted on
                        for i in range(len(self.bot.data["artContestThemeSuggestions"])):
                            emoji = str(i + 1) + "\ufe0f\u20e3"
                            await poll_message.add_reaction(emoji)

                        # Resets the list of reactions that is being kept to make sure people can only vote 1 thing
                        self.bot.data["artContestThemePollReactions"] = {}

                        
                        # Creates a new message for showing suggested theemes
                        suggestions_channel: discord.TextChannel = before.guild.get_channel(self.bot.data["artContestThemeSuggestionsChannel"])
                        suggestion_embed = discord.Embed(title="Use /art suggest_theme <theme> in another channel to suggested a theme!", description="Current Suggestions:", colour=discord.Colour.dark_gold())
                        suggestion_embed.set_author(name="Theme Suggestions", icon_url=self.bot.user.avatar)
                        suggestion_embed.add_field(name="PLACE HOLDER", value="-Father Fridge", inline=False)
                        
                        suggestion_message = await suggestions_channel.send(embed=suggestion_embed)

                        self.bot.data["artContestThemeSuggestionsMessage"] = suggestion_message.id
                        self.bot.data["artContestThemeSuggestions"] = {str(self.bot.user.id): "PLACE HOLDER"} # clears the theme suggestions
                        write_json_data(self.bot.data)

                        # New scheduled event for theme annoucement                   
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

                        # Gets the winning theme from the poll
                        poll_message: discord.Message  = await announcements_channel.fetch_message(self.bot.data["artContestThemePollMessage"])
                        reactions = sorted(poll_message.reactions, key=lambda reaction: reaction.count, reverse=True) # sorts the reactions based on count from high to low
                        highest_count = reactions[0].count
                        winning_emojis = [] 
                        # makes a list of the most reacted emojis
                        for reaction in reactions:
                            if reaction.count == highest_count:
                                winning_emojis.append(reaction.emoji)

                        # gets the winning theme's name and handels more then 1 winner
                        embed = poll_message.embeds[0]
                        suggested_themes = embed.description.split("\n")
                        winning_emoji = choice(winning_emojis) # randomly selects a emoji from the winning emojis list
                        for suggested_theme in suggested_themes:
                            if suggested_theme.startswith(winning_emoji):
                                winning_theme = suggested_theme.replace(winning_emoji + " ", "") # removes the emoji from the start of the text

                        await announcements_channel.send(f"THEME: {winning_theme} WON! (WIP TEXT)")

                        self.bot.data["artContestTheme"] = winning_theme
                        write_json_data(self.bot.data)


                        # WIP code for sumbiting art here?

                        # Create New Event For Art Contest
                        time_now = discord.utils.utcnow()
                        time_start = time_now.replace(minute=(time_now.minute + 1)) # this needs to be done diffrently since this breaks if the event ends at 59min

                        time_day = next_weekday(time_now, 6) # sets the time to coming sunday
                        time_end = time_day.replace(hour=22, minute=59, second=0)

                        await before.guild.create_scheduled_event(
                            name=f"Art Contest: {winning_theme}",
                            description="make art ig",
                            start_time=time_start,
                            end_time=time_end,
                            privacy_level=PrivacyLevel.guild_only,
                            entity_type=EntityType.external,
                            location="TEST TES TEST"
                        )


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
# make sure people can only vote on 1 thing on the theme voting (PROBLAY JUST SWITCH TO BUTTONS OR MAYBE NOT IM TO TIRED) 

# theme override command (admins only)

# final thing once everything works: make sure it pings and clean up the text
    


                        # ### TIRED ASH NOTES: NEEDS a way of handeling the poll if there no suggestions and when theres no post
                        # # New Suggestions Forum Post for theme
                        # forum_channel: discord.ForumChannel = before.guild.get_channel(self.bot.data["artContestThemeSuggestionsChannel"])
                        # old_thread = forum_channel.get_thread(self.bot.data["artContestThemeSuggestionsThread"])
                        # if isinstance(old_thread, discord.Thread): # Checks if the old thread exist 
                        #     # Making Poll code here
                        #     messages = [message async for message in old_thread.history(limit=50)]
                        #     messages = messages[1:-1] # Removes the post name and description from the messages
                        #     messages.reverse()
                            
                        #     # Creates theme_idea list with the first 9 entrys of the messages
                        #     theme_idea: list = []
                        #     i = 0
                        #     while i <= min(8, len(messages)):
                        #         theme_idea.append(messages[i].content)
                        #         i += 1
                            
                        #     await old_thread.edit(name=f"OLD Theme Suggestions: {theme}", archived=True, locked=True, pinned=False) # Close old thread for theme suggestions 
                        
                        # else:
                        #     theme_idea: list = ["there were 0 themes suggested (or the bot broke)"]

                        # print(theme_idea)

                        # await forum_channel.create_thread(name="Theme Suggestions", content="WORDS HERE")
                        # self.bot.data["artContestThemeSuggestionsThread"] = forum_channel.last_message_id
                        # write_json_data(self.bot.data)