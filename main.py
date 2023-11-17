# Importing Dependencies
import json
import os.path
import random
import base64
import discord
from discord import app_commands
from discord.app_commands import Group, command
from discord.ext import commands
import asyncio
import logging
from typing import Any, List, Optional, Literal


# Conts
HANDLER = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
with open("token.txt", "r") as file:
    TOKEN = file.read()

OWNER_USERIDS = [461084048337403915]
NOT_OWNER_MESSAGE = "thy are not the one that shaped me"

# bot variables
if os.path.isfile("./in_dev.txt"):
    activity = discord.Activity(name="IN DEV (WONT SAFE!!)", type=discord.ActivityType.streaming)
else:
    activity = discord.Activity(name="over all", type=discord.ActivityType.watching)



# Setting up Discord Bot Manager Class and Command Handler
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), activity=activity)

# data gets stored in json so should be used for saved data (like settings)
bot.data = {
    "joinRole": 1171095238929039360,
    "webtoons": ["https://www.webtoons.com/en/thriller/school-bus-graveyard/list?title_no=2705"],
    "reactionRoles": {},
    "wordEmojis": {"cheese": "🧀"},
}


# cog loading (gets called just before bot.run)
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

# json write
def write_json_data():
    data_json = json.dumps(bot.data)
    with open("data.json", "w") as file:
        file.write(data_json)

# json read
def read_json_data():
    with open("data.json", "r") as file:
        fileContents = file.read()

    data = json.loads(fileContents)

    return data

# update data
def update_data():
    data_json = read_json_data()
    for key in data_json:
        bot.data[key] = data_json[key]

# remove oudated vars in data.json
def remove_outdated_data():
    data_json = read_json_data()
    for key in list(data_json):
        if not key in bot.data:
            del data_json[key]
    
    data_json = json.dumps(data_json)
    with open("data.json", "w") as file:
        file.write(data_json)

#sets the data to the data in the data.json
if os.path.isfile("./data.json"):
    remove_outdated_data()
    update_data()
write_json_data()


# Define a simple View that gives us a confirmation menu
class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=3)
        self.value = None
    
        @discord.ui.button(label="disable me")
        async def disable_me_button(self, interaction, button):
            button.disabled = True # set the disabled value 
            await interaction.response.edit_message(view=self)

        async def on_timeout(self) -> None:
            print("timed out...")
            await self.disable_all_items()

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Cancelling', ephemeral=True)
        self.value = False
        self.stop()

class Dropdown(discord.ui.Select):
    def __init__(self):

        # Set the options that will be presented inside the dropdown
        options = [
            discord.SelectOption(label='Red', description='Your favourite colour is red', emoji='🟥'),
            discord.SelectOption(label='Green', description='Your favourite colour is green', emoji='🟩'),
            discord.SelectOption(label='Blue', description='Your favourite colour is blue', emoji='🟦'),
        ]

        # The placeholder is what will be shown when no option is chosen
        # The min and max values indicate we can only pick one of the three options
        # The options parameter defines the dropdown options. We defined this above
        super().__init__(placeholder='Choose your favourite colour...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        # Use the interaction object to send a response message containing
        # the user's favourite colour or choice. The self object refers to the
        # Select object, and the values attribute gets a list of the user's
        # selected options. We only want the first one.
        
        await interaction.response.send_message(f'Your favourite colour is {self.values[0]}')

class JoinRoleDropdown(discord.ui.RoleSelect):
    def __init__(self):
        role = bot.data["joinRole"] # TODO this needs to get the role so it doesnt just say the role id but i have no idea how and im going insane
        super().__init__(placeholder=f"Join Role: {role}", min_values=1, max_values=1)
        
    async def callback(self, interaction: discord.Interaction) -> Any:
        roles: List[discord.Role] = self.values
        selected_roles = [
            f"Name: {role.name}, ID: {role.id}"
            for role in roles
        ]
        await interaction.response.send_message(
            f"{interaction.user.mention} selected the following roles:\n" + "\n".join(selected_roles)
        )

class JoinRoleView(discord.ui.View):
    def __init__(self):
        super().__init__()

        # Adds the dropdown to our view object.
        self.add_item(JoinRoleDropdown())



    


# start up message
@bot.event
async def on_ready():
    print("--------------")
    print(f"{bot.user} is CONNECTED!")
    print(f"with cogs: {bot.extensions}")

#sync commands
@bot.command()
async def sync_cmds(ctx):
    if ctx.author.id in OWNER_USERIDS:
        print("Synced Commands")
        await bot.tree.sync()
        await ctx.send("Command tree sycned")
    else:
        await ctx.send(NOT_OWNER_MESSAGE)

#shutdown bot
@bot.command()
async def shutdown(ctx):
    if ctx.author.id in OWNER_USERIDS:
        print("Shutting Down from command")
        await ctx.send("Shutting Down")
        write_json_data()
        await bot.close()
    else:
        await ctx.send(NOT_OWNER_MESSAGE)



# on chat message
@bot.event
async def on_message(message:discord.Message):
    #needed to make bot.command() still work
    await bot.process_commands(message)

    #checks that its not a command
    if message.content.startswith(bot.command_prefix):
        return

    #if bot mentioned
    if bot.user.mentioned_in(message):
        await message.author.send("what doth thee wanteth?")

    #checks if its not the bot that send it
    if message.author != bot.user:
        #word emojis
        for key in bot.data["wordEmojis"]:
            if key in message.content.lower():
                for emoji in bot.data["wordEmojis"][key]:
                    await message.add_reaction(emoji)

 
# on member join
@bot.event
async def on_member_join(member): #discord.Member
    role = member.guild.get_role(bot.data["joinRole"])
    await member.add_roles(role, reason="Joined guild")

# on raw reaction add
@bot.event
async def on_raw_reaction_add(payload):
    # checks if it not the bot
    if payload.user_id != bot.user.id:
        # reaction role add
        message_id = str(payload.message_id) 
        if message_id in bot.data["reactionRoles"]:
            if payload.emoji.name in bot.data["reactionRoles"][message_id]:
                guild = bot.get_guild(payload.guild_id)
                await guild.get_member(payload.user_id).add_roles(guild.get_role(bot.data["reactionRoles"][message_id][payload.emoji.name]), reason="ReactionRole")

# on raw reaction remove
@bot.event
async def on_raw_reaction_remove(payload):
    # checks if it not the bot
    if payload.user_id != bot.user.id:
        #reaction role remove
        message_id = str(payload.message_id) 
        if message_id in bot.data["reactionRoles"]:
            if payload.emoji.name in bot.data["reactionRoles"][message_id]:
                guild = bot.get_guild(payload.guild_id)
                await guild.get_member(payload.user_id).remove_roles(guild.get_role(bot.data["reactionRoles"][message_id][payload.emoji.name]), reason="ReactionRole")


# /COMMANDS

# set join role
@bot.tree.command(name="join_role", description="Sets the role given on guild join")
@app_commands.checks.has_permissions(manage_roles=True)
async def join_role(interaction: discord.Interaction):
    view = JoinRoleView()
    await interaction.response.send_message("text", view=view, ephemeral=True)

@join_role.error
async def say_error(interaction: discord.Interaction, error):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("You do not have the perms for this (L bozo go cry about it)!", ephemeral=True)


# button test
@bot.tree.command(name="button", description="button test")
async def button(interaction: discord.Interaction):
    view = Confirm()
    await interaction.response.send_message("text", view=view)
    
    await view.wait()
    await view.disable_me_button()

    if view.value is None:
        print('Timed out...')
    elif view.value:
        print('Confirmed...')
    else:
        print('Cancelled...')


asyncio.run(load_cogs())
bot.run(TOKEN, log_handler=HANDLER, log_level=logging.DEBUG)


# to do:

#-needs to be added:

# poll command! DONE
# poll command response with results when times up

# list wmojis DONE

# help command

# add a settings menu thats just a lot of drop downs????
# color setting? (for views)

# event helper??? (like discord EVENTS the button at the top of all the channels)

# apps (like right click and then it shows apps)





