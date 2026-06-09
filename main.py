import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os

TOKEN = os.getenv("TOKEN")

# ✅ CRIAR BOT PRIMEIRO (OBRIGATÓRIO)
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

ytdl = yt_dlp.YoutubeDL({'format': 'bestaudio'})

fila = {}

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🔥 Online: {bot.user}")

# =========================
# BUSCA
# =========================
async def buscar(q):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None,
        lambda: ytdl.extract_info(f"ytsearch:{q}", download=False)
    )
    return data['entries'][0]['url'], data['entries'][0]['title']

# =========================
# PLAYER
# =========================
async def proxima(guild):
    if guild not in fila or not fila[guild]:
        return

    url, titulo = fila[guild].pop(0)

    voice = guild.voice_client
    source = await discord.FFmpegOpusAudio.from_probe(url)

    voice.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(proxima(guild), bot.loop))

# =========================
# COMANDOS (AGORA OK)
# =========================
@bot.tree.command(name="tocar", description="Tocar música")
async def tocar(interaction: discord.Interaction, pesquisa: str):
    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send("❌ Entra num canal de voz")

    canal = interaction.user.voice.channel
    voice = interaction.guild.voice_client

    if not voice:
        voice = await canal.connect()

    url, titulo = await buscar(pesquisa)

    if interaction.guild not in fila:
        fila[interaction.guild] = []

    fila[interaction.guild].append((url, titulo))

    if not voice.is_playing():
        await proxima(interaction.guild)

    await interaction.followup.send(f"🎵 {titulo}")

@bot.tree.command(name="parar")
async def parar(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("🛑 Parado")

# =========================
bot.run(TOKEN)
