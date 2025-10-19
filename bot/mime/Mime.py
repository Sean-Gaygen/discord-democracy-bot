import discord
import datetime

from discord.ext import tasks, commands
from dataclasses import dataclass
import random
from _init import *

@dataclass
class Mime:

    change_state_in: datetime.datetime = datetime.datetime.now()
    is_asleep = True

intents = discord.Intents.all()
mentions = discord.AllowedMentions.all()

bot = commands.Bot(command_prefix='..........', intents=intents, allowed_mentions=mentions, enable_raw_presence=True)


async def wake_up():

    await bot.change_presence(status=discord.Status.online)


async def nighty_night():

    await bot.change_presence(status=discord.Status.idle, activity=None)

@bot.event
async def on_raw_presence_update(ctx: discord.RawPresenceUpdateEvent):

    try:

        print(ctx.activities)

        if not Mime.is_asleep and len(ctx.activities) > 0:

            await bot.change_presence(status=discord.Status.online, activity=ctx.activities[0])

    except Exception as e:

        print(e)



@bot.event
async def on_typing(channel: discord.TextChannel, user: discord.Member, when: datetime.datetime):

    if not user.id == 821178560467042324 and not Mime.is_asleep:

        await channel.typing()


@bot.event
async def on_raw_reaction_add(ctx: discord.RawReactionActionEvent) -> None:

    guild: discord.Guild= bot.get_guild(ctx.guild_id)
    channel: discord.TextChannel = guild.get_channel(ctx.channel_id)

    try:

        message: discord.Message = await channel.fetch_message(ctx.message_id)

        await message.add_reaction(ctx.emoji)

    except (discord.errors.Forbidden, discord.errors.NotFound) as e:

        pass


@bot.event
async def on_raw_reaction_remove(ctx: discord.RawReactionActionEvent):

    guild: discord.Guild = bot.get_guild(ctx.guild_id)
    channel: discord.TextChannel = guild.get_channel(ctx.channel_id)

    try:

        message: discord.Message = await channel.fetch_message(ctx.message_id)

        for i in message.reactions:

            if i.me and i.count == 1:

                await i.remove(await guild.fetch_member(821178560467042324))

    except (discord.errors.Forbidden, discord.errors.NotFound) as e:

        pass


@bot.event
async def on_ready():

    check_sleep_status.start()


@tasks.loop(minutes=10)
async def check_sleep_status():

    if datetime.datetime.now() < Mime.change_state_in:

        return

    next_state_change_hours: int = random.choice(range(12, 18) if Mime.is_asleep else range(6, 12))
    Mime.change_state_in = datetime.datetime.now() + datetime.timedelta(hours=next_state_change_hours)

    print(f"Is asleep {not Mime.is_asleep}, changing in {next_state_change_hours} hours")

    if Mime.is_asleep:

        await wake_up()

    else:

        await nighty_night()

    Mime.is_asleep = not Mime.is_asleep
    
bot.run(TOKEN)
