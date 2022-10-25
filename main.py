import lavaplayer
import discord
import json
from discord.ext import commands

with open("config.json", "r") as file:
    jsonData = json.load(file)

TOKENjs = jsonData["token"]
hostjs = jsonData["host"]

TOKEN = TOKENjs
PREFIX = "?"

bot = commands.Bot(commands.when_mentioned_or(PREFIX), enable_debug_events=True, intents=discord.Intents.all())

lavalink = lavaplayer.LavalinkClient(
    host=hostjs,
    port=5464,
    password="votabot",
    user_id=1033812615417307146,
    is_ssl=False
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

@bot.command(help="Připoj se do kanálu")
async def join(ctx: commands.Context):
    await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
    await lavalink.wait_for_connection(ctx.guild.id)


@bot.command(help="Odpoj se z kanálu")
async def leave(ctx: commands.Context):
    await ctx.guild.change_voice_state(channel=None)
    await lavalink.wait_for_remove_connection(ctx.guild.id)


@bot.command(help="Pustí song")
async def play(ctx: commands.Context, *, query: str):
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
    queue = lavalink.queue(ctx.guild.id)
    if not queue:
        return await ctx.send("Žádné songy v queue.")
    tracks = [f"**{i + 1}.** {t.title}" for (i, t) in enumerate(queue)]
    await ctx.send("\n".join(tracks))




@bot.event

#
#This section took from https://github.com/HazemMeqdad/lavaplayer/blob/master/examples/dpy_base_v2/bot.py
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
