import discord
from discord import app_commands
from discord.ext import commands
import re
from typing import Optional
from bot_config import NO_PERMS_MESSAGE


class ReactionRole(commands.GroupCog, name="reactionrole"):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        super().__init__()  # this is now required in this context.

    ## LISTERNERS
    # role give
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        # checks if it not the bot
        if payload.user_id != self.bot.user.id:
            if payload.emoji.id == None:
                emoji = payload.emoji.name
            else:
                emoji = str(payload.emoji.id)

            role_id_records = await self.bot.pool.fetch(f"""
                SELECT role_id FROM reaction_roles
                WHERE message_id = {payload.message_id} AND emoji = $1;
                """, emoji)
            
            print(role_id_records)
            roles = [discord.Object(record["role_id"]) for record in role_id_records]
            await payload.member.add_roles(*roles, reason="Reaction Role")

    # role remove
    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        # checks if it not the bot
        if payload.user_id != self.bot.user.id:
            if payload.emoji.id == None:
                emoji = payload.emoji.name
            else:
                emoji = str(payload.emoji.id)

            role_id_records = await self.bot.pool.fetch(f"""
                SELECT role_id FROM reaction_roles
                WHERE message_id = {payload.message_id} AND emoji = $1;
                """, emoji)
            
            roles = [discord.Object(record["role_id"]) for record in role_id_records]
            await self.bot.get_guild(payload.guild_id).get_member(payload.user_id).remove_roles(*roles, reason="Reaction Role")



    ## COMMANDS
    # reacton role add
    @app_commands.command(name="add", description="add a reaction role (needs to be used in the channel the msg is in)")
    @app_commands.checks.has_permissions(administrator=True)
    async def reaction_role_add(self, interaction:discord.Interaction, message_id: str, emoji: str, role: discord.Role):
        message_id = int(message_id)
        message = self.bot.get_partial_messageable(interaction.channel_id, guild_id=interaction.guild_id).get_partial_message(message_id)

        await message.add_reaction(emoji)

        if "<:" in emoji:
            emoji_name = re.sub(r'<.+?:', '', emoji[:-1])
        else:
            emoji_name = emoji

        await self.bot.pool.execute(f"""
        INSERT INTO reaction_roles
        (guild_id, message_id, emoji, role_id, channel_id)
        VALUES ({interaction.guild_id}, {message_id}, $1, {role.id}, {interaction.channel_id});
        """, emoji_name)

        await interaction.response.send_message(f"channel: https://discord.com/channels/{interaction.guild_id}/{interaction.channel_id}, message: https://discord.com/channels/{interaction.guild_id}/{interaction.channel_id}/{message_id}, emoji: {emoji} with role: @{role} has been ADDED", ephemeral=True, suppress_embeds=True)
        

    @reaction_role_add.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True)
        

    # reaction role remove
    @app_commands.command(name="remove", description="remove a reaction role (needs to be used in the channel the msg is in)")
    @app_commands.checks.has_permissions(administrator=True)
    async def reaction_role_remove(self, interaction:discord.Interaction, message_id: str, emoji: Optional[str]):
        message_id = int(message_id)
        message = self.bot.get_partial_messageable(interaction.channel_id, guild_id=interaction.guild_id).get_partial_message(message_id)
        if type(emoji) == str:
            await message.clear_reaction(emoji)
            if "<:" in emoji:
                await self.bot.pool.execute(f"DELETE FROM reaction_roles WHERE message_id = {message_id} AND emoji = $1;", re.sub(r'<.+?:', '', emoji[:-1]))
            else:
                await self.bot.pool.execute(f"DELETE FROM reaction_roles WHERE message_id = {message_id} AND emoji = $1;", emoji)

            
            await interaction.response.send_message(f"channel: https://discord.com/channels/{interaction.guild_id}/{interaction.channel.id}, message: https://discord.com/channels/{interaction.guild_id}/{interaction.channel.id}/{message_id} with emoji: {emoji} has been REMOVED", ephemeral=True, suppress_embeds=True)
        
        else:
            await message.clear_reactions()
            await self.bot.pool.execute(f"DELETE FROM reaction_roles WHERE message_id = {message_id};")
            await interaction.response.send_message(f"all reactionroles on message: https://discord.com/channels/{interaction.guild_id}/{interaction.channel.id}/{message_id} in channel https://discord.com/channels/{interaction.guild_id}/{interaction.channel.id} have been REMOVED", ephemeral=True, suppress_embeds=True)
        
    @reaction_role_remove.error
    async def say_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.MissingPermissions):
            await interaction.response.send_message(NO_PERMS_MESSAGE, ephemeral=True)

    
    # reaction role list TODO this could be imporved by showing what roles every emoji gives
    @app_commands.command(name="list", description="lists the reaction roles")
    async def reaction_role_list(self, interaction:discord.Interaction):
        text = "list of reaction roles:\n"
        
        records = await self.bot.pool.fetch(f"""
        SELECT channel_id, message_id FROM reaction_roles
        WHERE guild_id = {interaction.guild_id};
        """, )

        for record in records:
            text += f"https://discord.com/channels/{interaction.guild_id}/{record['channel_id']}/{record['message_id']}\n"
        
        await interaction.response.send_message(text, ephemeral=True, suppress_embeds=True)
    

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ReactionRole(bot))