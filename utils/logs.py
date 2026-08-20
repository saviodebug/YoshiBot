import discord


async def enviar_log(
    bot,
    channel_id,
    titulo,
    descricao=None,
    cor=None,
    campos=None,
    arquivo=None
):

    if not channel_id:
        return

    canal = bot.get_channel(channel_id)

    if canal is None:
        print(
            f"❌ Canal de log {channel_id} não encontrado."
        )
        return

    if cor is None:
        cor = discord.Color.from_rgb(
            0,
            170,
            255
        )

    embed = discord.Embed(
        title=titulo,
        description=descricao,
        color=cor,
        timestamp=discord.utils.utcnow()
    )

    if campos:

        for campo in campos:

            embed.add_field(
                name=campo["name"],
                value=campo["value"],
                inline=campo.get(
                    "inline",
                    False
                )
            )

    embed.set_footer(
        text="Yoshizinho City • Sistema de Logs"
    )

    try:

        if arquivo:

            await canal.send(
                embed=embed,
                file=arquivo
            )

        else:

            await canal.send(
                embed=embed
            )

    except discord.Forbidden:

        print(
            f"❌ Sem permissão para enviar log em {canal}."
        )