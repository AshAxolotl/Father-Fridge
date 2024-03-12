# Importing Dependencies
import json
import os.path
import discord
from discord.ext import commands
import logging
import asyncpg
from bot_config import TOKEN, DEBUG, OWNER_USERIDS, COMMAND_PREFIX, SQL_IP, SQL_USER, SQL_PASSWORD, SQL_PORT


# Bot Activity
if DEBUG:
    activity = discord.CustomActivity(name="IN DEV")
    status = discord.Status.dnd
    log_level = logging.DEBUG
else:
    activity = discord.Activity(name="over all", type=discord.ActivityType.watching)
    status = discord.Status.online
    log_level = logging.ERROR


# Setting up Discord Bot Manager Class and Command Handler
bot = commands.Bot(command_prefix=COMMAND_PREFIX, intents=discord.Intents.all(), activity=activity, status=status) #, activity=activity, status=status
bot.owner_ids.update(OWNER_USERIDS)
# data gets stored in json so should be used for saved data (like settings)
bot.data = {
    "joinRole": 1171095238929039360, # DONE
    "webtoons": ["https://www.webtoons.com/en/thriller/school-bus-graveyard/list?title_no=2705"], # REMOVE?
    "reactionRoles": {},  # DONE
    "wordEmojis": {"cheese": "🧀"}, # DONE
    "quoteChannel": 1185960968140898325, # DONE
    "artContestActive": False,
    "artContestTheme": "Cheese",
    "artContestSubmissionsChannel": 1202694627031785503,
    "artContestAnnouncementsChannel": 1142861396875432028,
    "artContestThemeSuggestionsChannel": 1201194360209944766,
    "artContestThemeSuggestionsMessage": 1201197417819820082,
    "artContestThemePollMessage": 0,
    "artContestThemePollReactions": {},
    "artContestThemeSuggestions": {"1171539759533920318": "PLACE HOLDER"}, # {botid: "PLACE HOLDER"}
    "artContestSubmissions": {},
    "artContestFormId": 0,
    "artContestRole": 1142856096369881188,
    "artContestResponderUri": ""
}

# cog loading
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

# sets the data to the data in the data.json
if os.path.isfile("./data.json"):
    remove_outdated_data()
    update_data()
write_json_data()



## BOT EVENTS
# setup hooks
@bot.event
async def setup_hook():
    await load_cogs()
    # Database
    bot.pool = await asyncpg.create_pool(dsn=f"postgres://{SQL_USER}:{SQL_PASSWORD}@{SQL_IP}:{SQL_PORT}/fatherfridgedb")
    await bot.pool.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            guild_id BIGINT PRIMARY KEY,
	        join_role_id BIGINT,
            join_message TEXT,
	        quote_channel_id BIGINT
        );
        CREATE TABLE IF NOT EXISTS wmojis (
            guild_id BIGINT,
            word TEXT,
            emoji TEXT
        );
        CREATE TABLE IF NOT EXISTS reaction_roles (
            guild_id BIGINT,
            message_id BIGINT,
            emoji TEXT,
            role_id BIGINT,
            channel_id BIGINT
        );
        CREATE TABLE IF NOT EXISTS server_name_suggestions (
            guild_id BIGINT,
            user_id BIGINT,
            name_suggestion TEXT,
            UNIQUE (guild_id, user_id)
        );
    """) # TODO art contest maybe just in settings?

# start up message
@bot.event
async def on_ready():
    print(f"{bot.user} is CONNECTED!")
    print("--------------")
    # print(f"with cogs: {bot.extensions}")



## CONTEXT MENUS (dont have good cog support so they here)
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



bot.run(TOKEN, log_handler=logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w'), log_level=log_level)