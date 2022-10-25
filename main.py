import lavaplayer
import discord
from discord.ext import commands

TOKEN = 'MTAzMzgxMjYxNTQxNzMwNzE0Ng.Glil6t.pxijtX5-cAdJpTMEvEEq99LXwRog2fqSSkG1KQ'
PREFIX = "?"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='?', intents=intents)


lavalink = lavaplayer.LavalinkClient(
    host="46.101.104.234",
    port=5464,
    password="votabot",
    user_id=1033812615417307146,
    is_ssl=False
)


@bot.event
async def close():
    for guild in bot.guilds:
        await guild.change_voice_state(channel=None)


@bot.command(name="help", aliases=["commands"], help="Shows all commands.")
async def help_commmand(ctx: commands.Context):
    embed = discord.Embed(title="Help", description="Toto je Help command", color=0x00ff00)
    embed.description = "\n".join(f"`{PREFIX}{command.name}`: {command.help}" for command in bot.commands)
    await ctx.send(embed=embed)

@bot.event
async def on_ready():
    lavalink.set_user_id(bot.user.id)
    lavalink.set_event_loop(bot.loop)
    lavalink.connect()
    print("Lavalink je ready")

@bot.command(help="Připoj se do kanálu")
async def join(ctx: commands.Context):
    await ctx.guild.change_voice_state(channel=ctx.author.voice.channel)
    await lavalink.wait_for_connection(ctx.guild.id)

@bot.command(name="Odpoj se z kanálu")
async def leave(ctx: commands.Context):
    await ctx.guild.change_voice_state(channel=None)
    await lavalink.wait_for_remove_connection(ctx.guild.id)


bot.run(TOKEN)
