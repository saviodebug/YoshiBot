import io

import discord


async def gerar_transcript(canal: discord.TextChannel) -> discord.File:
    linhas = [
        f"TRANSCRIPT - #{canal.name}",
        "=" * 70,
        ""
    ]

    async for mensagem in canal.history(
        limit=None,
        oldest_first=True
    ):
        horario = mensagem.created_at.strftime(
            "%d/%m/%Y %H:%M:%S UTC"
        )

        linhas.append(
            f"[{horario}] {mensagem.author} ({mensagem.author.id})"
        )

        if mensagem.clean_content:
            linhas.append(mensagem.clean_content)
        else:
            linhas.append("[sem texto]")

        if mensagem.attachments:
            linhas.append("Anexos:")

            for anexo in mensagem.attachments:
                linhas.append(
                    f"- {anexo.filename}: {anexo.url}"
                )

        if mensagem.embeds:
            linhas.append(
                f"Embeds na mensagem: {len(mensagem.embeds)}"
            )

        linhas.append("-" * 70)

    conteudo = "\n".join(linhas)

    buffer = io.BytesIO(
        conteudo.encode("utf-8")
    )

    return discord.File(
        fp=buffer,
        filename=f"transcript-{canal.name}.txt"
    )
