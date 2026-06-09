import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp
import asyncio
import os
import random
from collections import deque

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# YTDL CONFIG (robusto)
# =========================
YTDL_OPTS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0"
}
ytdl = yt_dlp.YoutubeDL(YTDL_OPTS)

FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn"
}

# =========================
# ESTADO POR SERVIDOR
# =========================
class Estado:
    def __init__(self):
        self.fila = deque()
        self.atual = None
        self.loop = "off"     # off | track | queue
        self.volume = 1.0
        self.autoplay = False

estados = {}

def get_estado(guild):
    if guild.id not in estados:
        estados[guild.id] = Estado()
    return estados[guild.id]

# =========================
# BUSCA ASSÍNCRONA
# =========================
async def buscar(query):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(
        None, lambda: ytdl.extract_info(query, download=False)
    )
    if "entries" in data:
        data = data["entries"][0]
    return {
        "url": data["url"],
        "titulo": data.get("title", "Sem título"),
        "web": data.get("webpage_url")
    }

# =========================
# PLAYER
# =========================
async def tocar_proxima(guild):
    estado = get_estado(guild)
    voice = guild.voice_client

    if not voice:
        return

    # loop track
    if estado.loop == "track" and estado.atual:
        estado.fila.appendleft(estado.atual)

    # se acabou a fila
    if not estado.fila:
        estado.atual = None
        return

    track = estado.fila.popleft()
    estado.atual = track

    src = await discord.FFmpegOpusAudio.from_probe(
        track["url"], **FFMPEG_OPTS
    )
    src = discord.PCMVolumeTransformer(src, volume=estado.volume)

    def _after(e):
        asyncio.run_coroutine_threadsafe(tocar_proxima(guild), bot.loop)

    voice.play(src, after=_after)

# =========================
# READY
# =========================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"🔥 Online: {bot.user}")

# =========================
# /TOCAR
# =========================
@bot.tree.command(name="tocar", description="Tocar música (nome ou link)")
async def tocar(interaction: discord.Interaction, pesquisa: str):
    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send("❌ Entra num canal de voz.")

    canal = interaction.user.voice.channel
    voice = interaction.guild.voice_client

    if not voice:
        voice = await canal.connect()

    track = await buscar(pesquisa)
    estado = get_estado(interaction.guild)
    estado.fila.append(track)

    if not voice.is_playing():
        await tocar_proxima(interaction.guild)

    await interaction.followup.send(f"🎵 Adicionado: {track['titulo']}")

# =========================
# CONTROLES
# =========================
@bot.tree.command(name="pausar", description="Pausar")
async def pausar(interaction: discord.Interaction):
    v = interaction.guild.voice_client
    if v and v.is_playing():
        v.pause()
        await interaction.response.send_message("⏸️ Pausado")

@bot.tree.command(name="retomar", description="Retomar")
async def retomar(interaction: discord.Interaction):
    v = interaction.guild.voice_client
    if v and v.is_paused():
        v.resume()
        await interaction.response.send_message("▶️ Retomado")

@bot.tree.command(name="pular", description="Pular")
async def pular(interaction: discord.Interaction):
    v = interaction.guild.voice_client
    if v:
        v.stop()
        await interaction.response.send_message("⏭️ Pulado")

@bot.tree.command(name="parar", description="Parar e sair")
async def parar(interaction: discord.Interaction):
    v = interaction.guild.voice_client
    if v:
        estados.pop(interaction.guild.id, None)
        await v.disconnect()
        await interaction.response.send_message("🛑 Parado")

# =========================
# FILA
# =========================
@bot.tree.command(name="fila", description="Ver fila")
async def fila(interaction: discord.Interaction):
    estado = get_estado(interaction.guild)

    if not estado.fila:
        return await interaction.response.send_message("📭 Fila vazia")

    msg = "\n".join(
        [f"{i+1}. {t['titulo']}" for i, t in enumerate(list(estado.fila)[:10])]
    )
    await interaction.response.send_message(f"📃 Fila:\n{msg}")

@bot.tree.command(name="remover", description="Remover da fila")
async def remover(interaction: discord.Interaction, posicao: int):
    estado = get_estado(interaction.guild)

    if posicao <= 0 or posicao > len(estado.fila):
        return await interaction.response.send_message("❌ Posição inválida")

    track = list(estado.fila)[posicao-1]
    estado.fila.remove(track)
    await interaction.response.send_message(f"🗑️ Removido: {track['titulo']}")

@bot.tree.command(name="embaralhar", description="Misturar fila")
async def embaralhar(interaction: discord.Interaction):
    estado = get_estado(interaction.guild)
    temp = list(estado.fila)
    random.shuffle(temp)
    estado.fila = deque(temp)
    await interaction.response.send_message("🔀 Embaralhado")

# =========================
# LOOP / VOLUME / NOW
# =========================
@bot.tree.command(name="loop", description="Loop (off, track, queue)")
async def loop_cmd(interaction: discord.Interaction, modo: str):
    estado = get_estado(interaction.guild)
    estado.loop = modo
    await interaction.response.send_message(f"🔁 Loop: {modo}")

@bot.tree.command(name="volume", description="Volume 0-100")
async def volume(interaction: discord.Interaction, valor: int):
    estado = get_estado(interaction.guild)
    estado.volume = max(0, min(valor, 100)) / 100

    v = interaction.guild.voice_client
    if v and v.source:
        v.source.volume = estado.volume

    await interaction.response.send_message(f"🔊 {valor}%")

@bot.tree.command(name="agora", description="Música atual")
async def agora(interaction: discord.Interaction):
    estado = get_estado(interaction.guild)
    if estado.atual:
        await interaction.response.send_message(f"🎶 {estado.atual['titulo']}")
    else:
        await interaction.response.send_message("Nada tocando")

# =========================
bot.run(TOKEN)
