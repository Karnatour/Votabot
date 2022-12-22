# TODO leave po čase

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
activity = discord.Activity(name="?help pro zobrazení příkazů", type=discord.ActivityType.playing)
# bot = commands.Bot(commands.when_mentioned_or("?","!"), enable_debug_events=True, intents=intents, activity=activity)
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
    elif isinstance(tracks, lavaplayer.PlayList):
        msg = await ctx.send("Playlist nalezen, přidávám do queue")
        await lavalink.add_to_queue(ctx.guild.id, tracks.tracks, ctx.author.id)
        await msg.edit(
            content="Playlist přidán do queue počet songů: {}, název: {}".format(len(tracks.tracks), tracks.name, ))
        return
    await lavalink.play(ctx.guild.id, tracks[0], ctx.author.id)
    ms_queue = tracks[0].length
    s_queue, ms_queue = divmod(ms_queue, 1000)
    m_queue, s_queue = divmod(s_queue, 60)

    await ctx.send(f"Přidáno do queue: {tracks[0].title} :hourglass: {int(m_queue):02d}:{int(s_queue):02d}")


@bot.command(help="Shuffle")
async def shuffle(ctx: commands.Context):
    await lavalink.shuffle(ctx.guild.id)
    await ctx.send("Shuffeled")


@bot.command(help="Právě hraje")
async def np(ctx: commands.Context):
    m_queue = await lavalink.queue(ctx.guild.id)
    if not m_queue:
        return await ctx.send("Žádný song nehraje.")
    sec_now = m_queue[0].position
    ms_queue = m_queue[0].length
    s_queue, ms_queue = divmod(ms_queue, 1000)
    min_queue, s_queue = divmod(s_queue, 60)
    min_now,sec_now = divmod(sec_now, 60)
    requester_id = m_queue[0].requester
    requester = bot.get_user(int(requester_id))
    new_var = f"{int(min_now):02d}:{int(sec_now):02d}/{int(min_queue):02d}:{int(s_queue):02d}"
    embed = discord.Embed(title=m_queue[0].title,url=m_queue[0].uri,color=0x00fbff)
    embed.set_author(name="Právě hraje:")
    embed.add_field(name=new_var, value=requester)
    await ctx.send(embed=embed)


@bot.command(help="Songy v queue")
async def queue(ctx: commands.Context):
    m_queue = await lavalink.queue(ctx.guild.id)
    if not m_queue:
        return await ctx.send("Žádné songy v queue.")
    embed = discord.Embed(title="Queue", color=0x00fbff)
    for tracks, m_queue in enumerate(m_queue):
        if tracks != 0:
            var = m_queue.length
            s_queue, ms_queue = divmod(var, 1000)
            m_queue, s_queue = divmod(s_queue, 60)
            requester_id = m_queue.requester
            requester = bot.get_user(int(requester_id))
            new_var = f"{int(m_queue):02d}:{int(s_queue):02d} {requester}"
            embed.add_field(name=str(tracks) + ") " + str(m_queue), value=" "+ str(new_var), inline=False)
    await ctx.send(embed=embed)


@bot.command(help="Skipne song")
async def skip(ctx: commands.Context):
    await lavalink.skip(ctx.guild.id)
    await ctx.send("Skipped!")


@bot.command(help="Vymaže queue")
async def clear(ctx: commands.Context):
    m_queue = await lavalink.queue(ctx.guild.id)
    length = len(m_queue)
    if not m_queue:
        return await ctx.send("Žádné songy v queue.")
    for i in range(length):
        try:
            await lavalink.remove(ctx.guild.id, 1)
        except:
            break
    await ctx.send("Queue smazána")


@bot.command(help="Vymaže song podle zadaného pořadí")
async def remove(ctx: commands.Context, index: int):
    m_queue = await lavalink.queue(ctx.guild.id)
    length = len(m_queue)
    if not m_queue:
        return await ctx.send("Nic nehraje")
    elif index == 0:
        return await ctx.send("Nelze smazat song který teď hraje")
    elif index >= length:
        return await ctx.send("Toto číslo je větší než počet songů v queue")
    else:
        await ctx.send(f"Song {m_queue[index].title} byl odebrán z queue")
        await lavalink.remove(ctx.guild.id, index)


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
