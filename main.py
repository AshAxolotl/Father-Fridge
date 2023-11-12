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
activity = discord.Activity(name="over all", type=discord.ActivityType.watching)
# Setting up Discord Bot Manager Class and Command Handler
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), activity=activity)

# data gets stored in json so should be used for saved data (like settings)
bot.data = {
    "joinRole": 1171095238929039360,
    "webtoons": ["https://www.webtoons.com/en/thriller/school-bus-graveyard/list?title_no=2705"],
    "reactionRoles": {}, # {'1171563367467585697': {'1172600729261846639': {'🔫': <Role id=1054483148903284846 name='membruh (guest)'>}}}
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


@bot.command()
async def sync_cmds(ctx):
    if ctx.author.id in OWNER_USERIDS:
        print("Synced Commands")
        await bot.tree.sync()
        await ctx.send("Command tree sycned")
    else:
        await ctx.send(NOT_OWNER_MESSAGE)

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

    #checks if its not the bot that send it
    if message.author != bot.user:
        for key in bot.data["wordEmojis"]:
            if key in message.content.lower():
                await message.add_reaction(bot.data["wordEmojis"][key])

 
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
        channel_id = str(payload.channel_id)
        if channel_id in bot.data["reactionRoles"]:
            message_id = str(payload.message_id) 
            if message_id in bot.data["reactionRoles"][channel_id]:
                if payload.emoji.name in bot.data["reactionRoles"][channel_id][message_id]:
                    guild = bot.get_guild(payload.guild_id)
                    await guild.get_member(payload.user_id).add_roles(guild.get_role(bot.data["reactionRoles"][channel_id][message_id][payload.emoji.name]), reason="ReactionRole")

# on raw reaction remove
@bot.event
async def on_raw_reaction_remove(payload):
    # checks if it not the bot
    if payload.user_id != bot.user.id:
        #reaction role remove
        channel_id = str(payload.channel_id)
        if channel_id in bot.data["reactionRoles"]:
            message_id = str(payload.message_id) 
            if message_id in bot.data["reactionRoles"][channel_id]:
                if payload.emoji.name in bot.data["reactionRoles"][channel_id][message_id]:
                    guild = bot.get_guild(payload.guild_id)
                    await guild.get_member(payload.user_id).remove_roles(guild.get_role(bot.data["reactionRoles"][channel_id][message_id][payload.emoji.name]), reason="ReactionRole")


# /COMMANDS

# webtoon 
@bot.tree.command(name="webtoon", description="sends you a webtoon recommendation THAT YOU SHALL READ")
async def webtoon(interaction: discord.Interaction):
    randomWebtoon = random.choice(bot.data["webtoons"])
    await interaction.response.send_message(f"I think you should read {randomWebtoon} but I exist in every instance of time so I do not know what you have read",ephemeral=True)


# recommand webtoon 
@bot.tree.command(name="recommand_webtoon", description="sends you a webtoon recommendation THAT YOU SHALL READ")
async def recommand_webtoon(interaction: discord.Interaction, webtoon: str):
    if webtoon.startswith("https://www.webtoons.com/en/") and "list?title_no" in webtoon:
        if webtoon in bot.data["webtoons"]:
            await interaction.response.send_message("I already know this!",ephemeral=True)
        else:
            bot.data["webtoons"].append(webtoon)
            write_json_data()
            await interaction.response.send_message(f"{webtoon} has been added to my infinite knowledge",ephemeral=True)
    else:
        await interaction.response.send_message("Thats not a webtoon you befoon (also make sure that it isnt a link to a chapter!))",ephemeral=True)


# set join role
@bot.tree.command(name="join_role", description="Sets the role given on guild join")
@app_commands.checks.has_permissions(manage_roles=True)
async def join_role(interaction: discord.Interaction):
    view = JoinRoleView()
    await interaction.response.send_message("text", view=view, ephemeral=True)

#@join_role.error
#async def say_error(interaction: discord.Interaction, error):
#    await interaction.response.send_message("Not allowed!", ephemeral=True)


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

# reacton role add
@bot.tree.command(name="reaction_role_add", description="add a reaction role")
@app_commands.checks.has_permissions(administrator=True)
async def reaction_role_add(interaction:discord.Interaction, channel: discord.TextChannel, message_id: str, emoji: str, role: discord.Role):
    message = await channel.fetch_message(int(message_id))
    await message.add_reaction(emoji)

    if str(channel.id) not in bot.data["reactionRoles"]:
        bot.data["reactionRoles"][str(channel.id)] = {}

    if message_id not in bot.data["reactionRoles"][str(channel.id)]:
        bot.data["reactionRoles"][str(channel.id)][message_id] = {}

    bot.data["reactionRoles"][str(channel.id)][message_id][emoji] = role.id
    await interaction.response.send_message(f"channel: {channel}, message_id: {message_id}, emoji: {emoji} with role: @{role} has been ADDED", ephemeral=True)
    print(bot.data["reactionRoles"])
    write_json_data()

# reaction role remove
@bot.tree.command(name="reaction_role_remove", description="remove a reaction role")
@app_commands.checks.has_permissions(administrator=True)
async def reaction_role_remove(interaction:discord.Interaction, channel: discord.TextChannel, message_id: str, emoji: str):
    message = await channel.fetch_message(int(message_id))
    role = bot.data["reactionRoles"][str(channel.id)][message_id][emoji]
    await message.clear_reaction(emoji)

    del bot.data["reactionRoles"][str(channel.id)][message_id][emoji]

    if not bot.data["reactionRoles"][str(channel.id)][message_id]:
        del bot.data["reactionRoles"][str(channel.id)][message_id]
    
    if not bot.data["reactionRoles"][str(channel.id)]:
        del bot.data["reactionRoles"][str(channel.id)]

    await interaction.response.send_message(f"channel: {channel}, message_id: {message_id}, emoji: {emoji} with role: {role} has been REMOVED", ephemeral=True)
    write_json_data()

# reaction role list
@bot.tree.command(name="reaction_role_list", description="lists the reaction roles (needs work)")
@app_commands.checks.has_permissions(administrator=True)
async def reaction_role_list(interaction:discord.Interaction):
    reaction_roles = bot.data["reactionRoles"]
    await interaction.response.send_message(f"{reaction_roles}", ephemeral=True)




asyncio.run(load_cogs())
bot.run(TOKEN, log_handler=HANDLER, log_level=logging.DEBUG)


# to do:
#-COGS / EXTENTIONS MOVE
# switch from client to bot? (idk if this is needed need to look into it more) DONE
# switch the sync commands from on message to how you would normaly with a bot DONE
# cog or extentions? DONE
# move commands to cogs
# command groups????



#good error msgs for when you dont have the perms

# add a settings menu thats just a lot of drop downs????
# help command



# event helper??? (like discord EVENTS the button at the top of all the channels)

# admin commands to mulpiled data??? (maybe just show)
# a admin command to shut down the bot DONE
