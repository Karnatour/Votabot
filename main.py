# TODO Kdyz zacne hrat dalsi song tak to nenapise ze zacal
# TODO Kdyz se prida dalsi song do queue tak to napise now playing misto added to queue
# TODO leave po čase
# TODO Proper queue

import json

import discord
import lavaplayer
from discord.ext import commands

with open("config_test.json", "r") as file:
    jsonData = json.load(file)

TOKENjs = jsonData["token"]
hostjs = jsonData["host"]

TOKEN = TOKENjs
PREFIX = "-"

intents = discord.Intents.all()
activity = discord.Activity(name="-help pro zobrazení příkazů",type=discord.ActivityType.playing)
bot = commands.Bot(commands.when_mentioned_or(PREFIX), enable_debug_events=True, intents=intents, activity=activity)

lavalink = lavaplayer.LavalinkClient(
    host=hostjs,
    port=5464,
    password="votabot",
    user_id=1033812615417307146,
)


@bot.event
async def close():
    for guild in bot.guilds:
        await guild.change_voice_state(channel=None)


@bot.event
async def on_ready():
    lavalink.set_user_id(bot.user.id)
    lavalink.set_event_loop(bot.loop)
    lavalink.connect()
    print("Lavalink je ready")


# @bot.command(name="help", help="Ukáže všechny commands")
# async def help(ctx: commands.Context):

@bot.command(help="Připojí se do kanálu")
async def join(ctx: commands.Context):
    if ctx.author.voice and ctx.author.voice.channel:
        await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
        await lavalink.wait_for_connection(ctx.guild.id)
    else:
        await ctx.send("Musíš být v kanále pro použití tohoto commandu")


@bot.command(help="Odpojí se z kanálu")
async def leave(ctx: commands.Context):
    if ctx.author.voice is None:
        await ctx.send("Musíš být v kanálu pro použití tohoto commandu")
    else:
        await ctx.guild.change_voice_state(channel=None)
        await lavalink.wait_for_remove_connection(ctx.guild.id)


@bot.command(help="Pustí song")
async def play(ctx: commands.Context, *, query: str):
    if not ctx.author.voice:
        await ctx.send("Musíš být v kanále pro použití tohoto commandu")
        return
    await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
    await lavalink.wait_for_connection(ctx.guild.id)
    tracks = await lavalink.auto_search_tracks(query)

    if not tracks:
        return await ctx.send("Nic nenalezeno")
    elif isinstance(tracks, lavaplayer.TrackLoadFailed):
        await ctx.send("Načtení songu selhalo poop code GG")
    # Playlist
    elif isinstance(tracks, lavaplayer.PlayList):
        msg = await ctx.send("Playlist nalezen, přidávám do queue")
        await lavalink.add_to_queue(ctx.guild.id, tracks.tracks, ctx.author.id)
        await msg.edit(content="Přidáno do queue songy: {}, názvy: {}".format(len(tracks.tracks), tracks.name))
        return
    await lavalink.play(ctx.guild.id, tracks[0], ctx.author.id)
    await ctx.send(f"Now playing: {tracks[0].title}")


@bot.command(help="Songy v queue")
async def queue(ctx: commands.Context):
    queue_v = await lavalink.queue(ctx.guild.id)
    if not queue_v:
        return await ctx.send("Žádné songy v queue.")
    embed = discord.Embed(title="Queue", description="Songy v queue jsou:", color=0x00fbff)
    for tracks, queue_v in enumerate(queue_v):
        if tracks == 0:
            embed.add_field(name="Právě hraje:", value=queue_v, inline=False)
        else:
            embed.add_field(name=str(tracks) + ")", value=queue_v, inline=False)
    await ctx.send(embed=embed)


@bot.command(help="Skipne song")
async def skip(ctx: commands.Context):
    await lavalink.skip(ctx.guild.id)
    await ctx.send("Skipped!")


@bot.command(help="Pauza")
async def pause(ctx: commands.Context):
    await lavalink.pause(ctx.guild.id, True)
    await ctx.send("Paused")


@bot.command(help="Pokračovat")
async def resume(ctx: commands.Context):
    await lavalink.pause(ctx.guild.id, False)
    await ctx.send("Pokračuji")


@bot.event
#
# This section took from https://github.com/HazemMeqdad/lavaplayer/blob/master/examples/dpy_base_v2/bot.py
#
async def on_socket_raw_receive(msg):
    data = json.loads(msg)

    if not data or not data["t"]:
        return
    if data["t"] == "VOICE_SERVER_UPDATE":
        guild_id = int(data["d"]["guild_id"])
        endpoint = data["d"]["endpoint"]
        token = data["d"]["token"]

        await lavalink.raw_voice_server_update(guild_id, endpoint, token)

    elif data["t"] == "VOICE_STATE_UPDATE":
        if not data["d"]["channel_id"]:
            channel_id = None
        else:
            channel_id = int(data["d"]["channel_id"])

        guild_id = int(data["d"]["guild_id"])
        user_id = int(data["d"]["user_id"])
        session_id = data["d"]["session_id"]

        await lavalink.raw_voice_state_update(
            guild_id,
            user_id,
            session_id,
            channel_id,
        )


bot.run(TOKEN)
