import discord
from discord.ext import commands
import yt_dlp
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# EVENTOS
# =========================
@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")

@bot.event
async def on_member_join(member):
    if member.guild.system_channel:
        await member.guild.system_channel.send(f"Bem-vindo {member.mention}!")

# =========================
# COMANDOS
# =========================
@bot.command()
async def ping(ctx):
    await ctx.send("Pong!")

# =========================
# MÚSICA
# =========================
ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio'})

@bot.command()
async def play(ctx, *, query):
    if not ctx.author.voice:
        return await ctx.send("Entre em um canal de voz!")

    channel = ctx.author.voice.channel
    voice = ctx.voice_client

    if not voice:
        voice = await channel.connect()

    info = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
    url = info['url']
    title = info['title']

    source = await discord.FFmpegOpusAudio.from_probe(url)
    voice.play(source)

    await ctx.send(f"Tocando: {title}")

@bot.command()
async def stop(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

bot.run(TOKEN)
