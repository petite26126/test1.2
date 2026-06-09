# =========================
# TOCAR
# =========================
@bot.tree.command(name="tocar", description="Tocar música pelo nome ou link")
async def tocar(interaction: discord.Interaction, pesquisa: str):
    await interaction.response.defer()

    if not interaction.user.voice:
        return await interaction.followup.send("❌ Entre em um canal de voz!")

    canal = interaction.user.voice.channel
    voz = interaction.guild.voice_client

    if not voz:
        voz = await canal.connect()

    url, titulo = await search(pesquisa)

    if interaction.guild not in queues:
        queues[interaction.guild] = {"list": [], "current": None}

    queues[interaction.guild]["list"].append((url, titulo))

    if not voz.is_playing():
        await play_next(interaction.guild)

    await interaction.followup.send(f"🎵 Adicionado: {titulo}")

# =========================
# PAUSAR
# =========================
@bot.tree.command(name="pausar", description="Pausar música")
async def pausar(interaction: discord.Interaction):
    voz = interaction.guild.voice_client
    if voz and voz.is_playing():
        voz.pause()
        await interaction.response.send_message("⏸️ Música pausada")

# =========================
# RETOMAR
# =========================
@bot.tree.command(name="retomar", description="Retomar música")
async def retomar(interaction: discord.Interaction):
    voz = interaction.guild.voice_client
    if voz and voz.is_paused():
        voz.resume()
        await interaction.response.send_message("▶️ Música retomada")

# =========================
# PULAR
# =========================
@bot.tree.command(name="pular", description="Pular música")
async def pular(interaction: discord.Interaction):
    voz = interaction.guild.voice_client
    if voz:
        voz.stop()
        await interaction.response.send_message("⏭️ Música pulada")

# =========================
# PARAR
# =========================
@bot.tree.command(name="parar", description="Parar e sair")
async def parar(interaction: discord.Interaction):
    voz = interaction.guild.voice_client
    if voz:
        queues[interaction.guild] = {"list": [], "current": None}
        await voz.disconnect()
        await interaction.response.send_message("🛑 Parado")

# =========================
# FILA
# =========================
@bot.tree.command(name="fila", description="Ver fila de músicas")
async def fila(interaction: discord.Interaction):
    q = queues.get(interaction.guild)

    if not q or not q["list"]:
        return await interaction.response.send_message("📭 Fila vazia")

    msg = "\n".join([f"{i+1}. {t[1]}" for i, t in enumerate(q["list"][:10])])
    await interaction.response.send_message(f"📃 Fila:\n{msg}")

# =========================
# REMOVER
# =========================
@bot.tree.command(name="remover", description="Remover música da fila")
async def remover(interaction: discord.Interaction, posicao: int):
    q = queues.get(interaction.guild)

    if not q or posicao <= 0 or posicao > len(q["list"]):
        return await interaction.response.send_message("❌ Posição inválida")

    removida = q["list"].pop(posicao-1)
    await interaction.response.send_message(f"🗑️ Removido: {removida[1]}")

# =========================
# EMBARALHAR
# =========================
@bot.tree.command(name="embaralhar", description="Misturar a fila")
async def embaralhar(interaction: discord.Interaction):
    q = queues.get(interaction.guild)

    if q:
        random.shuffle(q["list"])
        await interaction.response.send_message("🔀 Fila embaralhada")

# =========================
# LOOP
# =========================
@bot.tree.command(name="loop", description="Loop da música (track ou off)")
async def loop(interaction: discord.Interaction, modo: str):
    loops[interaction.guild] = modo
    await interaction.response.send_message(f"🔁 Loop ativado: {modo}")

# =========================
# VOLUME
# =========================
@bot.tree.command(name="volume", description="Alterar volume (0-100)")
async def volume(interaction: discord.Interaction, valor: int):
    valor = max(0, min(valor, 100)) / 100
    volumes[interaction.guild] = valor
    await interaction.response.send_message(f"🔊 Volume: {int(valor*100)}%")

# =========================
# AGORA
# =========================
@bot.tree.command(name="agora", description="Música atual")
async def agora(interaction: discord.Interaction):
    q = queues.get(interaction.guild)

    if q and q["current"]:
        await interaction.response.send_message(f"🎶 Tocando: {q['current'][1]}")
    else:
        await interaction.response.send_message("Nada tocando")
