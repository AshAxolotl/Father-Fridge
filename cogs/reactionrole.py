import discord
from discord import app_commands
from discord.ext import commands
import json
from typing import Optional


class ReactionRole(commands.GroupCog, name="reactionrole"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required in this context.
    
    # reacton role add
    @app_commands.command(name="add", description="add a reaction role (needs to be used in the channel the msg is in)")
    @app_commands.checks.has_permissions(administrator=True)
    async def reaction_role_add(self, interaction:discord.Interaction, message_id: str, emoji: str, role: discord.Role):
        channel = interaction.channel
        message = await channel.fetch_message(int(message_id))
        
        #checks if its a server emoji and makes it so its only the name
        if "<:" in emoji:
            await interaction.response.send_message("for server emojis just do the name!", ephemeral=True)
            return


        if message_id not in self.bot.data["reactionRoles"]:
            self.bot.data["reactionRoles"][message_id] = {}

        self.bot.data["reactionRoles"][message_id][emoji] = role.id
        self.bot.data["reactionRoles"][message_id]["channel"] = channel.id

        write_json_data(self.bot.data)
        await message.add_reaction(emoji)
        await interaction.response.send_message(f"channel: {channel}, message_id: {message_id}, emoji: {emoji} with role: @{role} has been ADDED", ephemeral=True)

    @reaction_role_add.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have the perms for this (L bozo go cry about it)!", ephemeral=True)
        

    # reaction role remove
    @app_commands.command(name="remove", description="remove a reaction role (needs to be used in the channel the msg is in)")
    @app_commands.checks.has_permissions(administrator=True)
    async def reaction_role_remove(self, interaction:discord.Interaction, message_id: str, emoji: Optional[str]):
        channel = interaction.channel
        message = await channel.fetch_message(int(message_id))
        if type(emoji) == str:
            role = self.bot.data["reactionRoles"][message_id][emoji]
            await message.clear_reaction(emoji)

            del self.bot.data["reactionRoles"][message_id][emoji]

            # checks if there are no emojis (reactionroles) left in the msg
            if self.bot.data["reactionRoles"][message_id] == {"channel": channel.id}:
                del self.bot.data["reactionRoles"][message_id]

            await interaction.response.send_message(f"channel: {channel}, message_id: {message_id}, emoji: {emoji} with role: {role} has been REMOVED", ephemeral=True)
        else:
            del self.bot.data["reactionRoles"][message_id]
            
            await message.clear_reactions()
            await interaction.response.send_message(f"all reactionroles on message_id: {message_id} in channel {channel} have been REMOVED", ephemeral=True)
        
        write_json_data(self.bot.data)
    
    @reaction_role_remove.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message("You do not have the perms for this (L bozo go cry about it)!", ephemeral=True)

    # reaction role list
    @app_commands.command(name="list", description="lists the reaction roles")
    async def reaction_role_list(self, interaction:discord.Interaction):
        text = "list of reaction roles:\n"
        for message_id in self.bot.data["reactionRoles"]:
            channel_id = self.bot.data["reactionRoles"][message_id]["channel"]
            text = text + "https://discord.com/channels/" + str(interaction.guild_id) + "/" + str(channel_id) + "/" + message_id + "\n"
        await interaction.response.send_message(text, ephemeral=True)
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRole(bot))

# json write (for cogs)
def write_json_data(data):
    data_json = json.dumps(data, indent=4)
    with open("data.json", "w") as file:
        file.write(data_json)
