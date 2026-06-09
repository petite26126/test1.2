import discord
from discord import app_commands
from discord.ext import commands
import wavelink
import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
LAVALINK_URL = os.getenv("LAVALINK_URL")
LAVALINK_PASSWORD = os.getenv("LAVALINK_PASSWORD")

# ===== SPOTIFY =====
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))

# ===== DISCORD =====
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ===== EVENTO READY =====
@bot.event
async def on_ready():
    print(f"🔥 Online: {bot.user}")

    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)} comandos sincronizados")
    except Exception as e:
        print(e)

    # conectar Lavalink
    node = wavelink.Node(
        uri=LAVALINK_URL,
        password=LAVALINK_PASSWORD
    )

    await wavelink.Pool.connect(client=bot, nodes=[node])
    print("🎵 Lavalink conectado!")

# ===== FUNÇÃO SPOTIFY -> YOUTUBE =====
async def spotify_para_youtube(query):
    if "spotify.com" in query:
        track = sp.track(query)
        nome = track["name"]
        artista = track["artists"][0]["name"]
        return f"{nome} {artista}"
    return query

# ===== COMANDO TOCAR =====
@bot.tree.command(name="tocar", description="Tocar música (nome ou link Spotify)")
async def tocar(interaction: discord.Interaction, musica: str):

    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send("❌ Entre em um canal de voz!")

    canal = interaction.user.voice.channel

    player: wavelink.Player
    player = interaction.guild.voice_client

    if not player:
        player = await canal.connect(cls=wavelink.Player)

    busca = await spotify_para_youtube(musica)

    tracks = await wavelink.Playable.search(busca)

    if not tracks:
        return await interaction.followup.send("❌ Música não encontrada!")

    track = tracks[0]

    await player.play(track)

    await interaction.followup.send(f"🎶 Tocando: **{track.title}**")

# ===== COMANDO PAUSAR =====
@bot.tree.command(name="pausar", description="Pausar música")
async def pausar(interaction: discord.Interaction):
    player: wavelink.Player = interaction.guild.voice_client

    if not player:
        return await interaction.response.send_message("❌ Nada tocando")

    await player.pause(True)
    await interaction.response.send_message("⏸️ Música pausada")

# ===== COMANDO RETOMAR =====
@bot.tree.command(name="retomar", description="Retomar música")
async def retomar(interaction: discord.Interaction):
    player: wavelink.Player = interaction.guild.voice_client

    if not player:
        return await interaction.response.send_message("❌ Nada tocando")

    await player.pause(False)
    await interaction.response.send_message("▶️ Música retomada")

# ===== COMANDO PULAR =====
@bot.tree.command(name="pular", description="Pular música")
async def pular(interaction: discord.Interaction):
    player: wavelink.Player = interaction.guild.voice_client

    if not player:
        return await interaction.response.send_message("❌ Nada tocando")

    await player.stop()
    await interaction.response.send_message("⏭️ Música pulada")

# ===== COMANDO SAIR =====
@bot.tree.command(name="sair", description="Desconectar do canal")
async def sair(interaction: discord.Interaction):
    player: wavelink.Player = interaction.guild.voice_client

    if not player:
        return await interaction.response.send_message("❌ Não estou conectado")

    await player.disconnect()
    await interaction.response.send_message("👋 Saí do canal")

# ===== START =====
bot.run(TOKEN)
