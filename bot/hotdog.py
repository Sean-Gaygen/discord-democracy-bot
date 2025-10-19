import _init
import discord
from discord_ids import *

intents: discord.Intents = discord.Intents.all()
mentions = discord.AllowedMentions.all()

client: discord.Client = discord.Client(intents=intents, mentions=mentions)

@client.event
async def on_message(ctx: discord.Message):
	"""
		Bots don't trigger "on_message" with their own message. Clients do, but
		we can't run two different event loops at once. Thus, the easiest way
		to add a hotdog react to every message sent by the bot is to have this
		discrete program running alongside the bot code.
	"""

	if ctx.author.id == DEMOCRACYBOT_USER_ID:  # TODO separate ids into separate files

		await ctx.add_reaction('🌭')

client.run(_init.TOKEN)