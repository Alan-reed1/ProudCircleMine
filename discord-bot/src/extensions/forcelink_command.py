import discord
import logging
import requests
import datetime

from util import local, mcign, embed_lib
from util.mcign import MCIGN
from discord import app_commands
from discord.ext import commands


class ForceLinkCommand(commands.Cog):
	def __init__(self, bot: commands.Bot):
		self.bot = bot

	def get_player(self, player_id):
		player = local.LOCAL_DATA.uuid_cache.get_player(player_id)
		if player is None:
			timestamp = datetime.datetime.now().timestamp()
			player = MCIGN(player_id)
			local.LOCAL_DATA.uuid_cache.add_player(player.uuid, player.name, timestamp)
		return player

	# Permissions Check
	def check_permission(self, user: discord.Interaction.user):
		request = local.LOCAL_DATA.cursor.execute("SELECT bot_admin_role_id FROM config").fetchone()[0]
		if request is None:
			return False
		if user.get_role(int(request)):
			return True
		return False

	@app_commands.command(name="forcelink", description="Forcelink a discord user and ign/uuid")
	@app_commands.describe(discord_id="Discord ID associated with minecraft username")
	@app_commands.describe(player="Uuid/Name of player to force link")
	async def force_link(self, interaction: discord.Interaction, discord_id: str, player: str):
		is_bot_admin = self.check_permission(interaction.user)
		if not is_bot_admin:
			await interaction.response.send_message(embed=embed_lib.InsufficientPermissionsEmbed())
			return

		try:
			discord_id = int(discord_id)
		except Exception as e:
			await interaction.response.send_message(embed=embed_lib.InvalidArgumentEmbed())

		mojang_player = MCIGN(player)

		# Make sure their account isn't already linked
		server_id = int(local.LOCAL_DATA.config.get_setting("server_id"))
		force_linked_discord_user = self.bot.get_guild(server_id).get_member(discord_id)
		if force_linked_discord_user is None:
			await interaction.response.send_message(embed=embed_lib.InvalidArgumentEmbed())
		link = local.LOCAL_DATA.discord_link.get_link(discord_id)
		if link is not None:  # AKA Their account IS linked
			already_linked_embed = discord.Embed(colour=discord.Colour(0x820529))
			already_linked_embed.description = "This account is already linked"
			await interaction.response.send_message(embed=already_linked_embed)
			return

		# Make API call to make sure username is linked to a valid Mojang account
		if mojang_player.uuid is None or mojang_player.name is None:
			await interaction.response.send_message(embed=embed_lib.InvalidMojangUserEmbed(player=player))
			return

		# Bypass api security check
		forced_discord_user_discrim = f"{force_linked_discord_user.name}#{force_linked_discord_user.discriminator}"
		local.LOCAL_DATA.discord_link.register_link(mojang_player.uuid, discord_id, forced_discord_user_discrim)
		successful_embed = embed_lib.SuccessfullyForceLinkedEmbed(mojang_player.name, force_linked_discord_user)
		await interaction.response.send_message(embed=successful_embed)


# class UnlinkCommand(commands.Cog):
# 	def __init__(self, bot: commands.Bot):
# 		self.bot = bot
#
# 	@app_commands.command(name="unlink", description="Unlink your discord and minecraft account")
# 	async def unlink(self, interaction: discord.Interaction):
# 		pass


# Add link and unlink commands to bot
async def setup(bot: commands.Bot):
	logging.debug("Adding cog: ForceLinkCommand")
	await bot.add_cog(ForceLinkCommand(bot))
	# logging.debug("Adding Cog: UnlinkCommand")
	# await bot.add_cog(UnlinkCommand(bot))
