import discord
from discord.ext import commands
import wavelink
import os

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# =========================
# CONEXÃO LAVALINK
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
# FUNÇÃO DE CONECTAR
# =========================
async def get_player(interaction):
    if not interaction.user.voice:
        await interaction.followup.send("❌ Entra num canal de voz primeiro.")
        return None

    channel = interaction.user.voice.channel

    if interaction.guild.voice_client:
        return interaction.guild.voice_client

    return await channel.connect(cls=wavelink.Player)

# =========================
# /TOCAR
# =========================
@bot.tree.command(name="tocar", description="Tocar música ou link (Spotify/YouTube)")
async def tocar(interaction: discord.Interaction, busca: str):
    await interaction.response.defer()

    player = await get_player(interaction)
    if not player:
        return

    tracks = await wavelink.Playable.search(busca)

    if not tracks:
        return await interaction.followup.send("❌ Nada encontrado.")

    track = tracks[0]

    await player.play(track)

    await interaction.followup.send(f"🎵 Tocando: **{track.title}**")

# =========================
# /PULAR
# =========================
@bot.tree.command(name="pular", description="Pular música")
async def pular(interaction: discord.Interaction):
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.stop()
        await interaction.response.send_message("⏭️ Música pulada")

# =========================
# /PARAR
# =========================
@bot.tree.command(name="parar", description="Parar e sair")
async def parar(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.disconnect()
        await interaction.response.send_message("🛑 Desconectado")

# =========================
# /PAUSAR
# =========================
@bot.tree.command(name="pausar", description="Pausar música")
async def pausar(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.pause()
        await interaction.response.send_message("⏸️ Pausado")

# =========================
# /RETOMAR
# =========================
@bot.tree.command(name="retomar", description="Retomar música")
async def retomar(interaction: discord.Interaction):
    vc = interaction.guild.voice_client
    if vc:
        await vc.resume()
        await interaction.response.send_message("▶️ Retomado")

bot.run(TOKEN)
