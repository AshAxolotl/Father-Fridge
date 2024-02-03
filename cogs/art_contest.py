from discord.ext import commands
import discord
from discord import EventStatus, app_commands, EntityType, PrivacyLevel
import datetime
import json
from random import choice
import google.google_forms_api as google_forms_api
from typing import Optional


# function for setting a datetime to a spesfic day next week
def next_weekday(d, weekday):
    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

def get_sorted_submissions_for_winner(self):
    # get form responses
    service = google_forms_api.create_service()
    results = service.forms().responses().list(formId=self.bot.data["artContestFormId"]).execute()
    
    # handle responses
    if "responses" in results: # checks if there where any responses on the form
        for response in results["responses"]:
            for answer_id in response["answers"]:
                for submission_key in self.bot.data["artContestSubmissions"]:
                    if answer_id[:7] == self.bot.data["artContestSubmissions"][submission_key]["id"]:
                        self.bot.data["artContestSubmissions"][submission_key]["points"] += int(response["answers"][answer_id]["textAnswers"]["answers"][0]["value"])
                        self.bot.data["artContestSubmissions"][submission_key]["max_points"] += 5
                        break
        
        # sort submissions based of score
        for submission_key in self.bot.data["artContestSubmissions"]:
            self.bot.data["artContestSubmissions"][submission_key]["score"] = self.bot.data["artContestSubmissions"][submission_key]["points"] / self.bot.data["artContestSubmissions"][submission_key]["max_points"]

        # creates a sorted list of tuples with [0] being the ID and [1] all of the data (most defintly not the best way of doing this but i have no idea how to do it beter and it works)
        sorted_list = sorted(self.bot.data["artContestSubmissions"].items(), key=lambda x: x[1]["score"], reverse=True)
        return sorted_list


class ArtContest(commands.GroupCog, name="art"):
    def __init__(self, bot):
        self.bot = bot

    # test command
    @app_commands.command(name="test", description="im going insane")
    async def test_art(self, interaction: discord.Interaction):
        # Create New Event For Winner Announcement
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
    @app_commands.command(name="suggest", description="suggest a theme!")
    async def suggest(self, interaction: discord.Interaction, theme: app_commands.Range[str, 1, 50]):
        # checks there arent already more suggestions then the cap
        if len(self.bot.data["artContestThemeSuggestions"]) < 9:
            self.bot.data["artContestThemeSuggestions"][str(interaction.user.id)] = theme
            # delets the place holder theme suggestion
            if str(self.bot.user.id) in self.bot.data["artContestThemeSuggestions"]:
                del self.bot.data["artContestThemeSuggestions"][str(self.bot.user.id)] 
            
            channel: discord.TextChannel = interaction.guild.get_channel(self.bot.data["artContestThemeSuggestionsChannel"])
            message: discord.Message  = await channel.fetch_message(self.bot.data["artContestThemeSuggestionsMessage"])
            embed: discord.Embed = message.embeds[0] # gets the embed that needs to be edited

            # clears all the fields to make sure that 1 person cant suggest more
            embed.clear_fields()
            for key in self.bot.data["artContestThemeSuggestions"]:
                username = self.bot.get_user(int(key)).name
                embed.add_field(name=self.bot.data["artContestThemeSuggestions"][key], value=f" -{username}", inline=False)

            await message.edit(embed=embed)
            await interaction.response.send_message(f"Successfully added {theme} to the suggestions in https://discord.com/channels/{interaction.guild_id}/{channel.id}", ephemeral=True)
            write_json_data(self.bot.data)
        else:
            await interaction.response.send_message(f"There are already to many suggestions so your suggestions: {theme} wasn't added (conntact ash about this)")
        
    # Submit Art command
    @app_commands.command(name="submit", description="submit art for the art contest")
    async def submit(self, interaction: discord.Interaction, art: discord.Attachment, title: Optional[str] = "N/A"):
        # Check if contest going on
        if not self.bot.data["artContestActive"]: 
            await interaction.response.send_message("There isnt any art event going on!", ephemeral=True)
            return
        
        # Check if valid file type
        if not art.content_type.split("/")[1].lower() in ["png", "gif", "jpg", "jpeg"]:
            await interaction.response.send_message("File type is not supported by google forms pls post a png, gif, jpg, jpeg! If your submission isnt one of does just post a random image and place the real submission in the forum thread and ping ash about it.", ephemeral=True)
            return

        user_id = str(interaction.user.id)
        channel: discord.ForumChannel = interaction.guild.get_channel(self.bot.data["artContestSubmissionsChannel"])
        thread_name = self.bot.data["artContestTheme"] +": "+ title +" -" + interaction.user.name
        file: discord.File = await art.to_file() # art attachment to file so it can be send
        
        if user_id in self.bot.data["artContestSubmissions"]:
            # Edit submission
            thread = channel.get_thread(self.bot.data["artContestSubmissions"][user_id]["thread_id"])
            # checks if title changed and if so change title
            if title != self.bot.data["artContestSubmissions"][user_id]["title"] and title != "N/A":
                thread = await thread.edit(name=thread_name)
                self.bot.data["artContestSubmissions"][user_id]["title"] = title

            # Edit attachment
            partial_message = thread.get_partial_message(self.bot.data["artContestSubmissions"][user_id]["message_id"])
            message = await partial_message.edit(attachments=[file]) 
            self.bot.data["artContestSubmissions"][user_id]["url"] = message.attachments[0].url
            
        else:
            # Create new submission
            id = str(len(self.bot.data["artContestSubmissions"])) * 7
            self.bot.data["artContestSubmissions"][user_id] = {"id": f"0{id[:6]}", "points": 0, "max_points": 0}
            thread = await channel.create_thread(name=thread_name, file=file)
            
            self.bot.data["artContestSubmissions"][user_id]["url"] = thread.message.attachments[0].url
            self.bot.data["artContestSubmissions"][user_id]["thread_id"] = thread.thread.id
            self.bot.data["artContestSubmissions"][user_id]["message_id"] = thread.message.id
            self.bot.data["artContestSubmissions"][user_id]["title"] = title
        
        
        self.bot.data["artContestSubmissions"][user_id]["username"] = interaction.user.name
        write_json_data(self.bot.data)
        await interaction.response.send_message(f"Successfully uploaded your submission to https://discord.com/channels/{interaction.guild_id}/{channel.id}", ephemeral=True)




    # make sure player can only vote for 1 theme (THIS ISNT GREAT SINCE ITS NOT SPAM PROOF MIGHT HAVE TO REPLACE IT WITH bUTTONS IDK???)
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

                        # Get channels
                        suggestions_channel: discord.TextChannel = before.guild.get_channel(self.bot.data["artContestThemeSuggestionsChannel"])
                        announcements_channel: discord.TextChannel = before.guild.get_channel(self.bot.data["artContestAnnouncementsChannel"])

                        # Get Winner
                        sorted_submissions = get_sorted_submissions_for_winner(self=self)

                        # announce winners
                        if sorted_submissions is not None:
                            winner_image_url = sorted_submissions[0][1]["url"]
                            winner_embed_text = ""
                            placement = 0
                            for submission in sorted_submissions:
                                placement += 1
                                points = submission[1]["points"]
                                max_points = submission[1]["max_points"]
                                winner_embed_text += f"{placement}. <@{submission[0]}> with {points}/{max_points}\n"

                            # WIP give winner post WINNER tag
                            
                        
                        else:
                            winner_embed_text = "there where no responses to the form :("
                            winner_image_url = ""
                            
                        winner_embed = discord.Embed(title="", description=winner_embed_text, colour=discord.Colour.dark_gold())
                        winner_embed.set_author(name=f"Voting Results: {theme}", url=self.bot.data["artContestResponderUri"])
                        winner_embed.set_image(url=winner_image_url)
                        winner_embed.set_footer(text="winner(s) shall be put on the fridge in 3-5 business day")
                        
                        await announcements_channel.send("<ping here>", embed=winner_embed)


                        # Create theme poll
                        poll_options_text: str = ""
                        number: int = 0
                        for key in self.bot.data["artContestThemeSuggestions"]:
                            number += 1
                            emoji = str(number) + "\ufe0f\u20e3" # number emojis 1️⃣
                            poll_option = self.bot.data["artContestThemeSuggestions"][key]
                            poll_options_text += f"{emoji} {poll_option}\n"
                        
                        poll_embed = discord.Embed(title="", description=poll_options_text, colour=discord.Colour.dark_gold())
                        poll_embed.set_author(name="Vote for the contest theme!")

                        poll_message = await announcements_channel.send(embed=poll_embed)
                        self.bot.data["artContestThemePollMessage"] = poll_message.id
                        
                        # Adds the emojis to the theme poll so it can be voted on
                        for i in range(len(self.bot.data["artContestThemeSuggestions"])):
                            emoji = str(i + 1) + "\ufe0f\u20e3"
                            await poll_message.add_reaction(emoji)

                        # Resets the list of reactions that is being kept to make sure people can only vote 1 thing
                        self.bot.data["artContestThemePollReactions"] = {}

                        
                        # Creates a new message for showing suggested themes
                        suggestion_embed = discord.Embed(title="Use /art suggest <theme> in another channel to suggested a theme!", description="Current Suggestions:", colour=discord.Colour.dark_gold())
                        suggestion_embed.set_author(name="Theme Suggestions")
                        suggestion_embed.add_field(name="PLACE HOLDER", value=" -Father Fridge", inline=False)
                        
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
                            description="Vote on the theme for the next art contest!",
                            start_time=time_start,
                            end_time=time_end,
                            privacy_level=PrivacyLevel.guild_only,
                            entity_type=EntityType.external,
                            location=f"https://discord.com/channels/{before.guild_id}/{announcements_channel.id}"
                        )


            # VOTING ON THEME DONE
            elif before.name == event_theme_announcement_name:
                if before.status == EventStatus.scheduled:
                    if after.status == EventStatus.active:
                        # Complets the theme announcement event so it gets removed
                        await after.edit(status=EventStatus.completed)

                        # Get channel
                        announcements_channel: discord.TextChannel = before.guild.get_channel(self.bot.data["artContestAnnouncementsChannel"])
                        submission_channel_id = self.bot.data["artContestSubmissionsChannel"]

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

                        await announcements_channel.send(f"<ping here> Theme \"{winning_theme}\" won the poll. Good luck with your art!", reference=poll_message)

                        self.bot.data["artContestTheme"] = winning_theme

                        # Resets the submissions
                        self.bot.data["artContestActive"] = True
                        self.bot.data["artContestSubmissions"] = {}

                        write_json_data(self.bot.data)

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
                            location=f"https://discord.com/channels/{before.guild_id}/{submission_channel_id}"
                        )


            # ART CONTEST DONE
            elif before.name == event_art_contest_name:
                if before.status == EventStatus.active:
                    if after.status == EventStatus.completed:
                        # Get channel
                        announcements_channel: discord.TextChannel = before.guild.get_channel(self.bot.data["artContestAnnouncementsChannel"])

                        # Creat the winner voting form
                        service = google_forms_api.create_service()

                        # Creates the initial Form
                        base_form = {"info": {"title": f"Art Contest: {theme}", "documentTitle": f"Art Contest: {theme}"}}
                        create_result = service.forms().create(body=base_form).execute()

                        # Update to the form to add description and base quistion
                        form_update = { 
                            "requests": [
                                {
                                    "updateFormInfo": {
                                        "info": {
                                            "description": "vote for the art contest!\nREMEMBER: DONT VOTE ON OWN ART AND DONT VOTE MORE THAN ONCE!",
                                        },
                                        "updateMask": "description",
                                    }
                                },
                                {
                                    "createItem": {
                                        "item": {
                                            "title": "what is your username?",
                                            "questionItem": {
                                                "question": {
                                                    "required": True,
                                                    "questionId":"0000aaaa",
                                                    "textQuestion": {
                                                        "paragraph": False
                                                    }
                                                }
                                            }
                                        },
                                        "location": {"index": 0},
                                    }
                                },
                            ]
                        }
                        
                        # adds all of the voting quistons to the update
                        for key in self.bot.data["artContestSubmissions"]:
                            username = self.bot.data["artContestSubmissions"][key]["username"]
                            title = self.bot.data["artContestSubmissions"][key]["title"]
                            id = self.bot.data["artContestSubmissions"][key]["id"]
                            form_update["requests"].append(
                                        {
                                    "createItem": {
                                        "item": {
                                            "title": f"{username}: {title}",
                                            "itemId": f"{id}a",
                                            "questionGroupItem": {
                                                "image": {
                                                    "sourceUri": self.bot.data["artContestSubmissions"][key]["url"],
                                                },
                                                "grid": {
                                                    "columns": {
                                                        "type": "RADIO",
                                                        "options": [{"value": "1"}, {"value": "2"}, {"value": "3"}, {"value": "4"}, {"value": "5"}]
                                                    }
                                                },
                                                "questions": [
                                                    {
                                                        "questionId": f"{id}b",
                                                        "rowQuestion": {"title": "How it look"}
                                                    },
                                                    {
                                                        "questionId": f"{id}c",
                                                        "rowQuestion": {"title": "Originality"}
                                                    },
                                                    {
                                                        "questionId": f"{id}d",
                                                        "rowQuestion": {"title": "How well does it use the theme"}
                                                    }
                                                ]
                                            }
                                        },
                                        "location": {"index": 1}
                                    }
                                },
                            )
                        
                        # Update the form with the form_update
                        service.forms().batchUpdate(formId=create_result["formId"], body=form_update).execute()

                        responer_uri = create_result["responderUri"]

                        self.bot.data["artContestResponderUri"] = responer_uri
                        self.bot.data["artContestFormId"] = create_result["formId"]
                        self.bot.data["artContestActive"] = False
                        write_json_data(self.bot.data)

                        await announcements_channel.send(f"<ping here> Vote on the art here: [google form]({responer_uri})")

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
                            location=responer_uri
                        )

                        

                    
                    
            
# set up cog
async def setup(bot):
    await bot.add_cog(ArtContest(bot))

# json write (for cogs)
def write_json_data(data):
  data_json = json.dumps(data, indent=4)
  with open("data.json", "w") as file:
    file.write(data_json)



#


# to do:
    
# winner handeling DONE
# add settings for art contest channels and role DONE
# clean up the code a bit? 
# text DONE

# commands to override theme start events and recount winner votes enz
# forum tags? 
# add pings (problay the final thing to do)


# make sure people can only vote on 1 thing on the theme voting (PROBLAY JUST SWITCH TO BUTTONS OR MAYBE NOT IM TO TIRED) 



