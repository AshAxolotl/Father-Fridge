from discord.ext import commands
import discord
from discord import EventStatus, app_commands, EntityType, PrivacyLevel
import datetime
from random import choice
import google_api_stuff as google_api_stuff
from googleapiclient.errors import HttpError
from typing import Optional, Literal
from bot_config import NO_PERMS_MESSAGE, BASE_ART_CONTEST_FORM_ID


# ArtContest Class
class ArtContest(commands.GroupCog, name="art"):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.event_theme_announcement_name = "Art Contest: theme announcement"
        self.event_theme_announcement_time = {"weekday": 1, "hour": 17, "minute": 0}
        self.event_winner_announcement_name = "Art Contest: winner announcement"
        self.event_winner_announcement_time = {"weekday": 0, "hour": 20, "minute": 0}
        self.event_art_contest_name = "Art Contest: "
        self.event_art_contest_time = {"weekday": 6, "hour": 22, "minute": 59}

    ## USER COMMANDS
    # Suggest Theme Command
    @app_commands.command(name="suggest", description="suggest a theme!")
    async def suggest(self, interaction: discord.Interaction, theme: app_commands.Range[str, 1, 50]):
        await self.bot.pool.execute(f"""
            INSERT INTO art_contest_theme_suggestions
            (guild_id, user_id, suggested_theme)
            VALUES ({interaction.guild_id}, {interaction.user.id}, $1)
            ON CONFLICT (guild_id, user_id) DO
                UPDATE SET suggested_theme = EXCLUDED.suggested_theme;
        """, theme)

        ids = await self.bot.pool.fetchrow(f"""
        SELECT art_contest_theme_suggestion_channel_id, art_contest_theme_suggestions_message_id FROM settings
        WHERE guild_id = {interaction.guild_id};
        """)

        suggestions = await self.bot.pool.fetch(f"""        
        SELECT user_id, suggested_theme FROM art_contest_theme_suggestions
        WHERE guild_id = {interaction.guild_id}
        """)
        
        await update_theme_suggestions_msg(guild=interaction.guild, channel_id=ids["art_contest_theme_suggestion_channel_id"], message_id=ids["art_contest_theme_suggestions_message_id"], suggestions=suggestions)

        await interaction.response.send_message(f"Successfully added {theme} to the theme suggestions in https://discord.com/channels/{interaction.guild_id}/{ids['art_contest_theme_suggestion_channel_id']}/{ids['art_contest_theme_suggestions_message_id']}", ephemeral=True, suppress_embeds=True)

    # Submit Art command
    @app_commands.command(name="submit", description="submit art for the art contest")
    async def submit(self, interaction: discord.Interaction, art: discord.Attachment, title: Optional[str] = "N/A"):

        ids_and_theme = await self.bot.pool.fetchrow(f"""
        SELECT art_contest_theme, art_contest_submissions_channel_id FROM settings
        WHERE guild_id = {interaction.guild_id};
        """)

        # Check if there is art contest going on
        if not any(event.name == (self.event_art_contest_name + ids_and_theme["art_contest_theme"]) and event.status == EventStatus.active for event in interaction.guild.scheduled_events): # TODO interaction.guild.scheduled events seems to return old events
            await interaction.response.send_message("There isnt any art contest going on!", ephemeral=True)
            return
        
        # Check if valid file type
        if not art.content_type.split("/")[1].lower() in ["png", "gif", "jpg", "jpeg"]:
            await interaction.response.send_message("File type is not supported by google forms pls post a png, gif, jpg, jpeg! If your submission isnt one of does just post a random image and place the real submission in the forum thread and ping ash about it.", ephemeral=True)
            return

        channel: discord.ForumChannel = interaction.guild.get_channel(ids_and_theme["art_contest_submissions_channel_id"])
        thread_name = ids_and_theme["art_contest_theme"] +": "+ title +" -" + interaction.user.name
        file: discord.File = await art.to_file() # art attachment to file so it can be send
        
        current_submissions = await self.bot.pool.fetch(f"""
            SELECT user_id, thread_id, message_id, title FROM art_contest_submissions
            WHERE guild_id = {interaction.guild_id}
        """)

        for submission in current_submissions:
            if submission["user_id"] == interaction.user.id:
                # Edit submissions
                thread = channel.get_thread(submission["thread_id"])
                # Edit title if there is a change
                if thread_name != thread.name and title != "N/A":
                    thread = await thread.edit(name=thread_name)
                else:
                    title = submission["title"]
                
                # Edit attachment
                partial_message = thread.get_partial_message(submission["message_id"])
                message = await partial_message.edit(attachments=[file])

                # Update values in database
                await self.bot.pool.execute(f"""
                    UPDATE art_contest_submissions
                    SET title = $1, image_url = $2
                    WHERE guild_id = {interaction.guild_id} AND user_id = {interaction.user.id}
                """, title, message.attachments[0].url)

                await interaction.response.send_message(f"Successfully updated your submission in https://discord.com/channels/{interaction.guild_id}/{thread.id}", ephemeral=True, suppress_embeds=True)
                return
            
        # Create new submission
        thread = await channel.create_thread(name=thread_name, file=file)
        await self.bot.pool.execute(f"""
            INSERT INTO art_contest_submissions
            (guild_id, user_id, thread_id, message_id, form_id, title, image_url)
            VALUES ({interaction.guild_id}, {interaction.user.id}, {thread.thread.id}, {thread.message.id}, $3, $1, $2)
        """, title, thread.message.attachments[0].url, (str(len(current_submissions)) * 7))
        
        await interaction.response.send_message(f"Successfully uploaded your submission to https://discord.com/channels/{interaction.guild_id}/{thread.thread.id}", ephemeral=True, suppress_embeds=True)


    ## ADMIN COMMANDS
    # create event command
    @app_commands.command(name="admin", description="(ADMIN ONLY)")
    @app_commands.checks.has_permissions(administrator=True)
    async def admin(self, interaction: discord.Interaction, action: Literal["create_winner_event", "create_theme_event", "create_active_event", "recount_winner", "create_form", "update_form", "start_new"]):
        await interaction.response.defer(ephemeral=True, thinking=True)
        if action == "create_theme_event":
            # New scheduled event for theme annoucement
            time = next_weekday(discord.utils.utcnow(), self.event_theme_announcement_time["weekday"]) # sets the time to coming tuesday
            await create_scheduled_event(
                guild=interaction.guild,
                name=self.event_theme_announcement_name,
                time_start=time.replace(hour=self.event_theme_announcement_time["hour"], minute=self.event_theme_announcement_time["minute"], second=0),
                time_end=time.replace(hour=self.event_theme_announcement_time["hour"], minute=self.event_theme_announcement_time["minute"], second=1)
            )
        
        elif action == "create_active_event":
            # Create New Event For Art Contest
            time = discord.utils.utcnow()
            await create_scheduled_event(
                guild=interaction.guild,
                name=f"{self.event_art_contest_name}THEME HERE",
                time_start=(time + datetime.timedelta(seconds=5)),
                time_end=next_weekday(time, self.event_art_contest_time["weekday"]).replace(hour=self.event_art_contest_time["hour"], minute=self.event_art_contest_time["minute"], second=0)
            )
            

        elif action == "create_winner_event":
            # Create New Event For Winner Announcement
            time = next_weekday(discord.utils.utcnow(), self.event_winner_announcement_time["weekday"]) # Sets the time to coming monday
            await create_scheduled_event(
                guild=interaction.guild,
                name=self.event_winner_announcement_name,
                time_start=time.replace(hour=self.event_winner_announcement_time["hour"], minute=self.event_winner_announcement_time["minute"], second=0),
                time_end=time.replace(hour=self.event_winner_announcement_time["hour"], minute=self.event_winner_announcement_time["minute"], second=1)
            )
        
        elif action == "create_form":
            # Create Form
            create_result = await create_form(pool=self.bot.pool, guild=interaction.guild)
            await send_winner_voting_form(self, interaction.guild_id, create_result)

        elif action == "update_form":
            # Update Form
            ids_and_theme = await self.bot.pool.fetchrow(f"""
            SELECT art_contest_form_id, art_contest_theme FROM settings
            WHERE guild_id = {interaction.guild_id};
            """)
            create_result = await update_form(pool=self.bot.pool, form_id=ids_and_theme["art_contest_form_id"], theme=ids_and_theme["art_contest_theme"], guild=interaction.guild)
            await send_winner_voting_form(self, interaction.guild_id, create_result)

        elif action == "start_new":
            channel_ids = await self.bot.pool.fetchrow(f"""
            SELECT art_contest_announcements_channel_id, art_contest_theme_suggestion_channel_id FROM settings
            WHERE guild_id = {interaction.guild_id};
            """)

            suggestions = await self.bot.pool.fetch(f"""        
            SELECT user_id, suggested_theme FROM art_contest_theme_suggestions
            WHERE guild_id = {interaction.guild_id}
            """)

            suggestions_message_id = await send_theme_suggestions_msg(interaction.guild, channel_ids["art_contest_theme_suggestion_channel_id"], suggestions)

            await self.bot.pool.execute(f"""
            UPDATE settings
            SET art_contest_theme_suggestions_message_id = {suggestions_message_id}
            WHERE guild_id = {interaction.guild_id}
            """)

            # Create New Event For Winner Announcement
            time = next_weekday(discord.utils.utcnow(), 0) # Sets the time to coming monday
            await create_scheduled_event(
                guild=interaction.guild,
                name=self.event_winner_announcement_name,
                time_start=time.replace(hour=self.event_winner_announcement_time["hour"], minute=self.event_winner_announcement_time["minute"], second=0),
                time_end=time.replace(hour=self.event_winner_announcement_time["hour"], minute=self.event_winner_announcement_time["minute"], second=1)
            )
            
        elif action == "recount_winner":
            ids_and_theme = await self.bot.pool.fetchrow(f"""
            SELECT art_contest_form_id, art_contest_theme, art_contest_responder_uri, art_contest_announcements_channel_id FROM settings
            WHERE guild_id = {interaction.guild_id};
            """)
            embed = await get_winner_embed(pool=self.bot.pool, guild_id=interaction.guild_id, form_id=ids_and_theme["art_contest_form_id"], theme=ids_and_theme["art_contest_theme"], form_url=ids_and_theme["art_contest_responder_uri"])
            channel = self.bot.get_partial_messageable(ids_and_theme["art_contest_announcements_channel_id"])
            await channel.send("(Vote Recount)", embed=embed)
        
        await interaction.followup.send(f"executed: {action}", ephemeral=True)
    
    @admin.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True)


    # Remove theme suggestions
    @app_commands.command(name="remove_theme_suggestion", description="remove a theme suggestion")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_theme_suggestion(self, interaction: discord.Interaction, theme: str):
        await self.bot.pool.execute(f"DELETE FROM art_contest_theme_suggestions WHERE guild_id = {interaction.guild_id} AND suggested_theme = $1", theme)
        
        ids = await self.bot.pool.fetchrow(f"""
        SELECT art_contest_theme_suggestion_channel_id, art_contest_theme_suggestions_message_id FROM settings
        WHERE guild_id = {interaction.guild_id};
        """)

        suggestions = await self.bot.pool.fetch(f"""        
        SELECT user_id, suggested_theme FROM art_contest_theme_suggestions
        WHERE guild_id = {interaction.guild_id}
        """)
        
        await update_theme_suggestions_msg(guild=interaction.guild, channel_id=ids["art_contest_theme_suggestion_channel_id"], message_id=ids["art_contest_theme_suggestions_message_id"], suggestions=suggestions)

        await interaction.response.send_message(f"Successfully REMOVED {theme} from the theme suggestions in https://discord.com/channels/{interaction.guild_id}/{ids['art_contest_theme_suggestion_channel_id']}/{ids['art_contest_theme_suggestions_message_id']}", ephemeral=True, suppress_embeds=True)
        
    @remove_theme_suggestion.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True)


    
    ## LISTENERS
    # Scheduled Event Changes 
    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        # Checks if the creator is the bot
        if before.creator == self.bot.user:

            # VOTING ON WINNER DONE
            if before.name == self.event_winner_announcement_name:            
                if before.status == EventStatus.scheduled:
                    if after.status == EventStatus.active:
                        # Complets the winner  announcement event so it gets removed
                        await after.edit(status=EventStatus.completed)

                        ids_and_theme = await self.bot.pool.fetchrow(f"""
                            SELECT art_contest_announcements_channel_id, art_contest_theme_suggestion_channel_id, art_contest_form_id, art_contest_theme, art_contest_responder_uri, art_contest_role_id FROM settings
                            WHERE guild_id = {after.guild_id};
                        """)

                        announcements_channel: discord.TextChannel = before.guild.get_channel(ids_and_theme["art_contest_announcements_channel_id"])

                        # Announce winner
                        winner_embed = await get_winner_embed(pool=self.bot.pool, guild_id=after.guild_id, form_id=ids_and_theme["art_contest_form_id"], theme=ids_and_theme["art_contest_theme"], form_url=ids_and_theme["art_contest_responder_uri"])
                        await announcements_channel.send(f"<@&{ids_and_theme['art_contest_role_id']}>", embed=winner_embed)

                        suggestions = await self.bot.pool.fetch(f"""        
                        SELECT suggested_theme FROM art_contest_theme_suggestions
                        WHERE guild_id = {after.guild_id}
                        LIMIT 9;
                        """)

                        # Create theme poll
                        if len(suggestions) == 0:
                            suggestions = [{"suggested_theme": "The bot being very sad (no one suggested a theme)"}]
                        poll_options_text = ""
                        number = 0
                        for suggestion in suggestions:
                            number += 1
                            emoji = str(number) + "\ufe0f\u20e3" # number emojis 1️⃣
                            poll_option = suggestion["suggested_theme"]
                            poll_options_text += f"{emoji} {poll_option}\n"
                        
                        poll_embed = discord.Embed(title="", description=poll_options_text, colour=discord.Colour.dark_gold())
                        poll_embed.set_author(name="Vote for the contest theme!")

                        poll_message = await announcements_channel.send(embed=poll_embed, silent=True)
                        
                        # Adds the emojis to the theme poll so it can be voted on
                        for i in range(len(suggestions)):
                            emoji = str(i + 1) + "\ufe0f\u20e3"
                            await poll_message.add_reaction(emoji)

                        
                        # Creates a new message for showing suggested themes
                        suggestions_message_id = await send_theme_suggestions_msg(after.guild, ids_and_theme["art_contest_theme_suggestion_channel_id"])

                        await self.bot.pool.execute(f"""
                            UPDATE settings
                            SET art_contest_theme_suggestions_message_id = {suggestions_message_id},
                                art_contest_poll_message_id = {poll_message.id}
                            WHERE guild_id = {after.guild_id};
                            DELETE FROM art_contest_theme_suggestions
                            WHERE guild_id = {after.guild_id};
                            """)

                        # New scheduled event for theme annoucement
                        time = next_weekday(discord.utils.utcnow(), self.event_theme_announcement_time["weekday"]) # sets the time to coming tuesday
                        await create_scheduled_event(
                            guild=after.guild,
                            name=self.event_theme_announcement_name,
                            time_start=time.replace(hour=self.event_theme_announcement_time["hour"], minute=self.event_theme_announcement_time["minute"], second=0),
                            time_end=time.replace(hour=self.event_theme_announcement_time["hour"], minute=self.event_theme_announcement_time["minute"], second=1)
                        )



            # VOTING ON THEME DONE
            elif before.name == self.event_theme_announcement_name:
                if before.status == EventStatus.scheduled:
                    if after.status == EventStatus.active:
                        # Complets the theme announcement event so it gets removed
                        await after.edit(status=EventStatus.completed)

                        ids = await self.bot.pool.fetchrow(f"""
                        SELECT art_contest_announcements_channel_id, art_contest_poll_message_id, art_contest_role_id FROM settings
                        WHERE guild_id = {after.guild_id};
                        """)

                        # Get channel
                        announcements_channel: discord.TextChannel = before.guild.get_channel(ids["art_contest_announcements_channel_id"])

                        # Gets the winning theme from the poll
                        poll_message: discord.Message = await announcements_channel.fetch_message(ids["art_contest_poll_message_id"])
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

                        await announcements_channel.send(f"<@&{ids['art_contest_role_id']}> Theme \"{winning_theme}\" won the poll. Good luck with your art!", reference=poll_message)

                        # update the theme
                        await self.bot.pool.execute(f"""
                            UPDATE settings
                            SET art_contest_theme = $1
                            WHERE guild_id = {after.guild_id};
                            """, winning_theme)
                        
                        # remove all old suggestions
                        await self.bot.pool.execute(f"DELETE FROM art_contest_submissions WHERE guild_id = {after.guild_id}")


                        # Create New Event For Art Contest
                        time = discord.utils.utcnow()
                        await create_scheduled_event(
                            guild=after.guild,
                            name=f"{self.event_art_contest_name}{winning_theme}",
                            time_start=(time + datetime.timedelta(seconds=5)),
                            time_end=next_weekday(time, self.event_art_contest_time["weekday"]).replace(hour=self.event_art_contest_time["hour"], minute=self.event_art_contest_time["minute"], second=0)
                        )


            # ART CONTEST DONE
            elif self.event_art_contest_name in before.name:
                if before.status == EventStatus.active:
                    if after.status == EventStatus.completed:
                        
                        create_result = await create_form(pool=self.bot.pool, guild=after.guild)

                        await send_winner_voting_form(self, after.guild_id, create_result)

                        # Create New Event For Winner Announcement
                        time = next_weekday(discord.utils.utcnow(), self.event_winner_announcement_time["weekday"]) # Sets the time to coming monday
                        await create_scheduled_event(
                            guild=after.guild,
                            name=self.event_winner_announcement_name,
                            time_start=time.replace(hour=self.event_winner_announcement_time["hour"], minute=self.event_winner_announcement_time["minute"], second=0),
                            time_end=time.replace(hour=self.event_winner_announcement_time["hour"], minute=self.event_winner_announcement_time["minute"], second=1)
                        )


## Functions
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

# send theme suggestions message
async def send_theme_suggestions_msg(guild: discord.Guild, suggestions_channel_id: int, suggestions = []) -> int:
    suggestions_channel: discord.TextChannel = guild.get_channel(suggestions_channel_id)
    # Creates a new message for showing suggested themes
    suggestion_embed = discord.Embed(title="Use /art suggest <theme> in another channel to suggested a theme!", description="Current Suggestions:", colour=discord.Colour.dark_gold())
    suggestion_embed.set_author(name="Theme Suggestions")
    for suggestion in suggestions:
        suggestion_embed.add_field(name=suggestion["suggested_theme"], value=f" -{discord.utils.get(guild.members, id=suggestion['user_id'])}", inline=False)
    
    suggestion_message = await suggestions_channel.send(embed=suggestion_embed, silent=True)
    return suggestion_message.id

# update theme suggestions message
async def update_theme_suggestions_msg(guild: discord.Guild, channel_id: int, message_id: int, suggestions):
    message: discord.Message  = await guild.get_channel(channel_id).fetch_message(message_id)
    embed: discord.Embed = message.embeds[0] # gets the embed that needs to be edited

    # clears all the fields to make sure that 1 person cant suggest more
    embed.clear_fields()
    for suggestion in suggestions:
        embed.add_field(name=suggestion["suggested_theme"], value=f" -{discord.utils.get(guild.members, id=suggestion['user_id'])}", inline=False)

    await message.edit(embed=embed)



## FORM FUNCTIONS
# get winner                   
async def get_results_embed_info(form_id: str, guild_id: int, pool) -> dict:
    """gets the art contest winner"""

    # gets the form results
    try:
        service = google_api_stuff.create_service(type="forms", version="v1")
        results = service.forms().responses().list(formId=form_id).execute()
    except HttpError as error:
        print(f"The Form for winner could not be found: {error}")
        return {"text": "there was a error getting the form votes :(", "image_url": ""}
    except:
        print(f"unknown error with getting for data for winning announcement")
        return {"text": "there was a error getting the form votes :(", "image_url": ""}
    
    if "responses" not in results:
        return {"text": "there where no responses to the form :(", "image_url": ""}


    # get submissions
    submissions_records = await pool.fetch(f"""
        SELECT user_id, form_id, image_url FROM art_contest_submissions
        WHERE guild_id = {guild_id}
    """)

    submissions_list = [dict(row) for row in submissions_records]
    for submission in submissions_list:
        submission["points"] = 0
        submission["max_points"] = 0
    

    # handle responses
    for response in results["responses"]:
        for answer_id in response["answers"]:
            for submission in submissions_list:
                if answer_id[:7] == submission["form_id"]:
                    submission["points"] += int(response["answers"][answer_id]["textAnswers"]["answers"][0]["value"])
                    submission["max_points"] += 5
                    break
    
    # sort submissions based of score
    for submission in submissions_list:
        submission["score"] = submission["points"] / submission["max_points"]

    # sorts the list based of the score from high to low
    submissions_list = sorted(submissions_list, key=lambda d: d["score"], reverse=True)
    # create the embed text
    winner_embed_text = ""
    placement = 0
    for submission in submissions_list:
        placement += 1
        winner_embed_text += f"{placement}. <@{submission['user_id']}> with {submission['points']}/{submission['max_points']}\n"

    return {"text": winner_embed_text, "image_url": submissions_list[0]["image_url"]}
    

async def get_winner_embed(pool, guild_id: int, form_id: str, theme: str, form_url: str):
    winner_embed_info = await get_results_embed_info(form_id=form_id, guild_id=guild_id, pool=pool) # returns a dict with {text: "", "image_url": ""}
        
    winner_embed = discord.Embed(title="", description=winner_embed_info["text"], colour=discord.Colour.dark_gold())
    winner_embed.set_author(name=f"Voting Results: {theme}", url=form_url)
    winner_embed.set_image(url=winner_embed_info["image_url"])
    winner_embed.set_footer(text="winner(s) shall be put on the fridge in 3-5 business day")
    
    return winner_embed






# Send winner voting form                     
async def send_winner_voting_form(self, guild_id: int, create_result):
    ids = await self.bot.pool.fetchrow(f"""
    SELECT art_contest_announcements_channel_id, art_contest_role_id FROM settings
    WHERE guild_id = {guild_id};
    """)
    announcements_channel = self.bot.get_partial_messageable(ids["art_contest_announcements_channel_id"])

    await announcements_channel.send(f"<@&{ids['art_contest_role_id']}> Vote on the art here: [google form]({create_result['responderUri']})")
                    
# Create Form
async def create_form(pool, guild: discord.Guild) -> dict:
    theme = await pool.fetchval(f"""
        SELECT art_contest_theme FROM settings
        WHERE guild_id = {guild.id};
        """)
    # copy the origin art contest form
    try:
        drive_service = google_api_stuff.create_service(type="drive", version="v3")
        copied_file_info = {"title": f"Art Contest: {theme}", "name": f"Art Contest: {theme}"}
        copy_results = drive_service.files().copy(fileId=BASE_ART_CONTEST_FORM_ID, body=copied_file_info).execute()

    except HttpError as error:
        print(f"An error occurred while coping the base form: {error}")
        return {"formId": "ERROR", "responderUri": "https://docs.google.com/forms/d/e/ERROR/viewform"}
    except:
        print("An unknown error occurred while coping the base form")
        return {"formId": "ERROR", "responderUri": "https://docs.google.com/forms/d/e/ERROR/viewform"}

    return await update_form(pool=pool, form_id=copy_results["id"], guild=guild, theme=theme)


async def update_form(pool, form_id, theme: str, guild: discord.Guild) -> dict:
    submissions = await pool.fetch(f"""
        SELECT user_id, form_id, title, image_url FROM art_contest_submissions
        WHERE guild_id = {guild.id}
    """)
    try: 
        # Update to the form to add description and base quistion
        forms_service = google_api_stuff.create_service(type="forms", version="v1")

        form_update = { 
            "requests": [
                {
                    "updateFormInfo": {
                        "info": {
                            "title": f"Art Contest: {theme}",
                            "description": "vote for the art contest!\nREMEMBER: DONT VOTE ON OWN ART AND DONT VOTE MORE THAN ONCE!",
                        },
                        "updateMask": "*",
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
        for submission in submissions:
            username = discord.utils.get(guild.members, id=submission["user_id"])
            title = submission["title"]
            id = submission["form_id"]
            form_update["requests"].append(
                        {
                    "createItem": {
                        "item": {
                            "title": f"{username}: {title}",
                            "itemId": f"{id}a",
                            "questionGroupItem": {
                                "image": {
                                    "sourceUri": submission["image_url"],
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
        forms_service.forms().batchUpdate(formId=form_id, body=form_update).execute()
        form_data = forms_service.forms().get(formId=form_id).execute()
        await pool.execute(f"""
        UPDATE settings
        SET art_contest_form_id = $1, art_contest_responder_uri = $2
        WHERE guild_id = {guild.id};
        """, form_data['formId'], form_data['responderUri'])

        return {"formId": form_data["formId"], "responderUri": form_data["responderUri"]}
    
    except HttpError as error:
        print(f"An error occurred while updating the form: {error}")
        return {"formId": "ERROR", "responderUri": "https://docs.google.com/forms/d/e/ERROR/viewform"}
    except:
        print("An unknown error occurred while updating the form")
        return {"formId": "ERROR", "responderUri": "https://docs.google.com/forms/d/e/ERROR/viewform"}

# set up cog
async def setup(bot):
    await bot.add_cog(ArtContest(bot))