import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import os

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# SYNC DOS SLASH COMMANDS
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"Bot online: {bot.user}")

# =========================
# SLASH COMMANDS
# =========================
@bot.tree.command(name="ping", description="Ver latência do bot")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("Pong!")

# =========================
# MÚSICA
# =========================
ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio'})

@bot.tree.command(name="play", description="Tocar música")
async def play(interaction: discord.Interaction, query: str):
    if not interaction.user.voice:
        return await interaction.response.send_message("Entre em um canal de voz!")

    channel = interaction.user.voice.channel
    voice = interaction.guild.voice_client

    if not voice:
        voice = await channel.connect()

    info = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]
    url = info['url']
    title = info['title']

    source = await discord.FFmpegOpusAudio.from_probe(url)
    voice.play(source)

    await interaction.response.send_message(f"Tocando: {title}")

@bot.tree.command(name="stop", description="Parar música")
async def stop(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("Parado!")

bot.run(TOKEN)
