import discord
from discord.ext import commands
import wavelink
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

TOKEN = os.getenv("TOKEN")

sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# LAVALINK
# =========================
@bot.event
async def on_ready():
    print(f"🔥 Online: {bot.user}")

    node = wavelink.Node(
        uri=os.getenv("LAVALINK_URL"),
        password=os.getenv("LAVALINK_PASSWORD")
    )

    await wavelink.Pool.connect(client=bot, nodes=[node])
    await bot.tree.sync()

# =========================
# UTIL
# =========================
def is_spotify(url):
    return "spotify.com" in url

def spotify_to_queries(url):
    queries = []

    if "track" in url:
        t = sp.track(url)
        queries.append(f"{t['name']} {t['artists'][0]['name']}")

    elif "playlist" in url:
        data = sp.playlist_items(url)
        for item in data['items']:
            track = item['track']
            if track:
                queries.append(f"{track['name']} {track['artists'][0]['name']}")

    elif "album" in url:
        data = sp.album_tracks(url)
        for t in data['items']:
            queries.append(f"{t['name']} {t['artists'][0]['name']}")

    return queries

async def get_player(interaction):
    if not interaction.user.voice:
        return None, "❌ Entra num canal de voz"

    canal = interaction.user.voice.channel

    if not interaction.guild.voice_client:
        player = await canal.connect(cls=wavelink.Player)
    else:
        player = interaction.guild.voice_client

    return player, None

# =========================
# PLAYER EVENTS
# =========================
@bot.listen("on_wavelink_track_end")
async def on_track_end(payload):
    player = payload.player

    if player.queue.is_empty:
        return

    next_track = await player.queue.get_wait()
    await player.play(next_track)

# =========================
# /TOCAR
# =========================
@bot.tree.command(name="tocar", description="Tocar música ou Spotify")
async def tocar(interaction: discord.Interaction, pesquisa: str):

    await interaction.response.defer()

    player, erro = await get_player(interaction)
    if erro:
        return await interaction.followup.send(erro)

    queries = []

    try:
        if is_spotify(pesquisa):
            queries = spotify_to_queries(pesquisa)
        else:
            queries = [pesquisa]
    except:
        return await interaction.followup.send("❌ Erro no Spotify")

    adicionadas = 0

    for q in queries:
        tracks = await wavelink.Playable.search(q)
        if tracks:
            await player.queue.put_wait(tracks[0])
            adicionadas += 1

    if not player.playing:
        track = await player.queue.get_wait()
        await player.play(track)

    await interaction.followup.send(f"🎵 {adicionadas} música(s) na fila")

# =========================
# /FILA
# =========================
@bot.tree.command(name="fila", description="Ver fila")
async def fila(interaction: discord.Interaction):
    player = interaction.guild.voice_client

    if not player or player.queue.is_empty:
        return await interaction.response.send_message("📭 Fila vazia")

    lista = "\n".join(
        [f"{i+1}. {t.title}" for i, t in enumerate(player.queue)]
    )

    await interaction.response.send_message(f"📜 Fila:\n{lista[:1900]}")

# =========================
# /SKIP
# =========================
@bot.tree.command(name="skip", description="Pular música")
async def skip(interaction: discord.Interaction):
    player = interaction.guild.voice_client

    if not player:
        return await interaction.response.send_message("❌ Nada tocando")

    await player.stop()
    await interaction.response.send_message("⏭ Pulado")

# =========================
# /PAUSAR
# =========================
@bot.tree.command(name="pausar", description="Pausar")
async def pausar(interaction: discord.Interaction):
    player = interaction.guild.voice_client

    if player:
        await player.pause()
        await interaction.response.send_message("⏸ Pausado")

# =========================
# /RESUMIR
# =========================
@bot.tree.command(name="resumir", description="Continuar")
async def resumir(interaction: discord.Interaction):
    player = interaction.guild.voice_client

    if player:
        await player.resume()
        await interaction.response.send_message("▶️ Continuando")

# =========================
# /PARAR
# =========================
@bot.tree.command(name="parar", description="Parar tudo")
async def parar(interaction: discord.Interaction):
    player = interaction.guild.voice_client

    if player:
        await player.disconnect()

    await interaction.response.send_message("🛑 Parado")

bot.run(TOKEN)
