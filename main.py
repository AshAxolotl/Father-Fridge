# Importing Dependencies
import json
import os.path
import random
import base64
import discord
from discord import app_commands
from discord.app_commands import Group, command
from discord.ext import commands, tasks
import asyncio
import logging
from typing import Any, List, Optional, Literal




# Bot Activity
if os.path.isfile("./in_dev.txt"):
    activity = discord.Activity(name="IN DEV (WONT SAFE!!)", type=discord.ActivityType.streaming)
else:
    activity = discord.Activity(name="over all", type=discord.ActivityType.watching)



# Setting up Discord Bot Manager Class and Command Handler
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all(), activity=activity)

# Conts
HANDLER = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
with open("token.txt", "r") as file:
    TOKEN = file.read()

bot.OWNER_USERIDS = [461084048337403915]
NOT_OWNER_MESSAGE = "thy are not the one that shaped me"


# data gets stored in json so should be used for saved data (like settings)
bot.data = {
    "joinRole": 1171095238929039360,
    "webtoons": ["https://www.webtoons.com/en/thriller/school-bus-graveyard/list?title_no=2705"],
    "reactionRoles": {},
    "wordEmojis": {"cheese": "🧀"},
    "quoteChannel": 1185960968140898325,
    "artContestAnnouncementsChannel": 1142861396875432028,
    "artContestTheme": "Cheese",
    "artContestThemeSuggestionsChannel": 1201194360209944766,
    "artContestThemeSuggestionsMessage": 1201197417819820082,
    "artContestThemePollMessage": 0,
    "artContestThemePollReactions": {},
    "artContestThemeSuggestions": {"1171539759533920318": "PLACE HOLDER"} # {botid: "PLACE HOLDER"}
}

# cog loading (gets called just before bot.run)
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


## JSON 
# json write
def write_json_data():
    data_json = json.dumps(bot.data, indent=4)
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



## BOT EVENTS
# start up message
@bot.event
async def on_ready():
    print("--------------")
    print(f"{bot.user} is CONNECTED!")
    # print(f"with cogs: {bot.extensions}")

#sync commands
@bot.command()
async def sync_cmds(ctx):
    if ctx.author.id in bot.OWNER_USERIDS:
        print("Synced Commands")
        await bot.tree.sync()
        await ctx.send("Command tree sycned")
    else:
        await ctx.send(NOT_OWNER_MESSAGE)

#shutdown bot
@bot.command()
async def shutdown(ctx):
    if ctx.author.id in bot.OWNER_USERIDS:
        print("Shutting Down from command")
        await ctx.send("Shutting Down")
        write_json_data()
        await bot.close()
    else:
        await ctx.send(NOT_OWNER_MESSAGE)

# on chat message
@bot.event
async def on_message(message:discord.Message):
    # needed to make bot.command() still work
    await bot.process_commands(message)



 
# on member join
@bot.event
async def on_member_join(member): #discord.Member
    role = member.guild.get_role(bot.data["joinRole"])
    await member.add_roles(role, reason="Joined guild")







## CONTEXT MENUS
# Quote context menu
@bot.tree.context_menu(name="quote")
async def quote(interaction: discord.Interaction, message: discord.Message):
    quote_channel = interaction.guild.get_channel(bot.data["quoteChannel"])

    embed = discord.Embed(
    colour=discord.Colour.dark_gold(),
    title=message.content,
    description=""
    )

    embed.add_field(name=f"-{message.author.name}", value="", inline=False)

    embed.set_footer(text=f"added by {interaction.user.name}")

    await quote_channel.send(embed=embed)
    await interaction.response.send_message(f"Added quote \"{message.content}\" by {message.author.name} in #{quote_channel}!", ephemeral=True)



# running the bot
asyncio.run(load_cogs())
bot.run(TOKEN, log_handler=HANDLER, log_level=logging.DEBUG)


# to do:

# check if the settings can handle a channel being deleted 

# beter profile pic for bot

# beter way of "syncing" the data.json or maybe even switching to sql or something IDK
# make a script to launch bot

# base 64 on the token?

#-needs to be added:

# poll command! DONE
# poll command response with results when times up



# add a settings menu thats just a lot of drop downs???? DONE

# event helper??? (like discord EVENTS the button at the top of all the channels)




