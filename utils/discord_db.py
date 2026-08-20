import asyncio
import re
from datetime import timedelta

import discord

from config import (
    LOG_TICKETS_CHANNEL_ID,
    LOG_INFRACOES_CHANNEL_ID,
    LOG_BOOSTERS_CHANNEL_ID,
    LOG_SISTEMA_CHANNEL_ID,
)


_STATE_MARKER = "YOSHI_DB_STATE_V1"
_state_lock = asyncio.Lock()


def parse_meta(texto: str | None) -> dict:
    if not texto:
        return {}

    meta = {}

    for parte in texto.split(";"):
        if "=" not in parte:
            continue

        chave, valor = parte.split("=", 1)
        meta[chave.strip()] = valor.strip()

    return meta


def embed_field(embed: discord.Embed, nome: str, padrao: str = "—") -> str:
    for campo in embed.fields:
        if campo.name == nome:
            return campo.value

    return padrao


async def _canal(bot, channel_id: int) -> discord.TextChannel:
    canal = bot.get_channel(channel_id)

    if canal is None:
        try:
            canal = await bot.fetch_channel(channel_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as erro:
            raise RuntimeError(
                f"Canal {channel_id} não encontrado ou inacessível: {erro}"
            ) from erro

    if not isinstance(canal, discord.TextChannel):
        raise RuntimeError(f"O ID {channel_id} não pertence a um canal de texto.")

    return canal


async def _obter_mensagem_estado(bot) -> discord.Message:
    canal = await _canal(bot, LOG_SISTEMA_CHANNEL_ID)

    try:
        fixadas = await canal.pins()
    except (discord.Forbidden, discord.HTTPException):
        fixadas = []

    for mensagem in fixadas:
        if (
            mensagem.author.id == bot.user.id
            and mensagem.content.startswith(_STATE_MARKER)
        ):
            return mensagem

    async for mensagem in canal.history(limit=300, oldest_first=False):
        if (
            mensagem.author.id == bot.user.id
            and mensagem.content.startswith(_STATE_MARKER)
        ):
            try:
                await mensagem.pin(reason="Estado persistente do Yoshi Bot")
            except (discord.Forbidden, discord.HTTPException):
                pass

            return mensagem

    mensagem = await canal.send(
        f"{_STATE_MARKER}\n"
        "ticket_counter:0"
    )

    try:
        await mensagem.pin(reason="Estado persistente do Yoshi Bot")
    except (discord.Forbidden, discord.HTTPException):
        pass

    return mensagem


async def obter_proximo_ticket_id(bot) -> int:
    async with _state_lock:
        mensagem = await _obter_mensagem_estado(bot)

        procura = re.search(
            r"ticket_counter:(\d+)",
            mensagem.content
        )

        atual = int(procura.group(1)) if procura else 0
        proximo = atual + 1

        await mensagem.edit(
            content=(
                f"{_STATE_MARKER}\n"
                f"ticket_counter:{proximo}"
            )
        )

        return proximo


async def registrar_ticket_aberto(
    bot,
    ticket_id: int,
    usuario: discord.Member,
    canal_ticket: discord.TextChannel,
    categoria: str,
    categoria_slug: str,
    resumo: str | None = None
):
    canal = await _canal(bot, LOG_TICKETS_CHANNEL_ID)

    embed = discord.Embed(
        title=f"🎫 Ticket #{ticket_id} aberto",
        description="Um novo atendimento foi criado.",
        color=discord.Color.green(),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="👤 Usuário",
        value=f"{usuario.mention}\n`{usuario.id}`",
        inline=True
    )

    embed.add_field(
        name="📂 Categoria",
        value=categoria,
        inline=True
    )

    embed.add_field(
        name="📍 Canal",
        value=f"{canal_ticket.mention}\n`{canal_ticket.id}`",
        inline=False
    )

    embed.add_field(
        name="📝 Resumo",
        value=resumo or "Não informado.",
        inline=False
    )

    embed.set_footer(
        text=(
            f"db=ticket;"
            f"ticket_id={ticket_id};"
            f"owner_id={usuario.id};"
            f"status=aberto;"
            f"categoria={categoria_slug}"
        )
    )

    await canal.send(embed=embed)


async def registrar_ticket_fechado(
    bot,
    ticket_id: int,
    dono_id: int,
    fechado_por: discord.Member,
    canal_nome: str,
    categoria_slug: str,
    transcript: discord.File | None = None
):
    canal = await _canal(bot, LOG_TICKETS_CHANNEL_ID)

    dono = fechado_por.guild.get_member(dono_id)

    embed = discord.Embed(
        title=f"🔒 Ticket #{ticket_id} fechado",
        description="O atendimento foi encerrado.",
        color=discord.Color.red(),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="👤 Dono do ticket",
        value=(
            f"{dono.mention}\n`{dono_id}`"
            if dono
            else f"`{dono_id}`"
        ),
        inline=True
    )

    embed.add_field(
        name="🔨 Fechado por",
        value=f"{fechado_por.mention}\n`{fechado_por.id}`",
        inline=True
    )

    embed.add_field(
        name="📂 Categoria",
        value=categoria_slug,
        inline=False
    )

    embed.add_field(
        name="📍 Canal",
        value=f"`#{canal_nome}`",
        inline=False
    )

    embed.set_footer(
        text=(
            f"db=ticket;"
            f"ticket_id={ticket_id};"
            f"owner_id={dono_id};"
            f"status=fechado;"
            f"categoria={categoria_slug};"
            f"closed_by={fechado_por.id}"
        )
    )

    if transcript is not None:
        await canal.send(embed=embed, file=transcript)
    else:
        await canal.send(embed=embed)


async def listar_logs_tickets(
    bot,
    ticket_id: int | None = None,
    owner_id: int | None = None
) -> list[tuple[discord.Message, dict, discord.Embed]]:
    canal = await _canal(bot, LOG_TICKETS_CHANNEL_ID)
    encontrados = []

    async for mensagem in canal.history(limit=None, oldest_first=True):
        if not mensagem.embeds:
            continue

        embed = mensagem.embeds[0]
        meta = parse_meta(embed.footer.text if embed.footer else None)

        if meta.get("db") != "ticket":
            continue

        if (
            ticket_id is not None
            and meta.get("ticket_id") != str(ticket_id)
        ):
            continue

        if (
            owner_id is not None
            and meta.get("owner_id") != str(owner_id)
        ):
            continue

        encontrados.append((mensagem, meta, embed))

    return encontrados


async def contar_infracoes_24h(bot, user_id: int) -> int:
    canal = await _canal(bot, LOG_INFRACOES_CHANNEL_ID)
    depois_de = discord.utils.utcnow() - timedelta(hours=24)
    total = 0

    async for mensagem in canal.history(
        limit=None,
        after=depois_de,
        oldest_first=False
    ):
        if not mensagem.embeds:
            continue

        embed = mensagem.embeds[0]
        meta = parse_meta(embed.footer.text if embed.footer else None)

        if (
            meta.get("db") == "infracao"
            and meta.get("user_id") == str(user_id)
        ):
            total += 1

    return total


async def registrar_infracao(
    bot,
    membro: discord.Member,
    motivo: str,
    tipo: str,
    acao: str,
    canal_origem: discord.abc.GuildChannel,
    conteudo: str = ""
):
    canal = await _canal(bot, LOG_INFRACOES_CHANNEL_ID)

    embed = discord.Embed(
        title="🚨 Infração registrada",
        description="O sistema de moderação registrou uma ocorrência.",
        color=discord.Color.orange(),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="👤 Usuário",
        value=f"{membro.mention}\n`{membro.id}`",
        inline=True
    )

    embed.add_field(
        name="⚠️ Motivo",
        value=motivo,
        inline=True
    )

    embed.add_field(
        name="🔨 Ação",
        value=acao,
        inline=False
    )

    embed.add_field(
        name="📍 Canal",
        value=getattr(canal_origem, "mention", f"`{canal_origem}`"),
        inline=False
    )

    if conteudo:
        embed.add_field(
            name="💬 Conteúdo removido",
            value=f"```{conteudo[:900]}```",
            inline=False
        )

    embed.set_footer(
        text=(
            f"db=infracao;"
            f"user_id={membro.id};"
            f"tipo={tipo};"
            f"acao={acao}"
        )
    )

    await canal.send(embed=embed)


async def listar_infracoes(
    bot,
    user_id: int | None = None
) -> list[tuple[discord.Message, dict, discord.Embed]]:
    canal = await _canal(bot, LOG_INFRACOES_CHANNEL_ID)
    encontrados = []

    async for mensagem in canal.history(limit=None, oldest_first=True):
        if not mensagem.embeds:
            continue

        embed = mensagem.embeds[0]
        meta = parse_meta(embed.footer.text if embed.footer else None)

        if meta.get("db") != "infracao":
            continue

        if (
            user_id is not None
            and meta.get("user_id") != str(user_id)
        ):
            continue

        encontrados.append((mensagem, meta, embed))

    return encontrados


async def registrar_booster(
    bot,
    membro: discord.Member,
    evento: str,
    cargo: discord.Role
):
    canal = await _canal(bot, LOG_BOOSTERS_CHANNEL_ID)

    comecou = evento == "iniciou"

    embed = discord.Embed(
        title=(
            "💜 Novo Booster"
            if comecou
            else "💔 Booster removido"
        ),
        description=(
            "Um membro começou a impulsionar o servidor."
            if comecou
            else "Um membro deixou de impulsionar o servidor."
        ),
        color=(
            discord.Color.purple()
            if comecou
            else discord.Color.red()
        ),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="👤 Usuário",
        value=f"{membro.mention}\n`{membro.id}`",
        inline=True
    )

    embed.add_field(
        name="🎁 Cargo",
        value=cargo.mention if comecou else cargo.name,
        inline=True
    )

    embed.set_footer(
        text=(
            f"db=booster;"
            f"user_id={membro.id};"
            f"evento={evento}"
        )
    )

    await canal.send(embed=embed)


async def listar_boosters(
    bot,
    user_id: int | None = None
) -> list[tuple[discord.Message, dict, discord.Embed]]:
    canal = await _canal(bot, LOG_BOOSTERS_CHANNEL_ID)
    encontrados = []

    async for mensagem in canal.history(limit=None, oldest_first=True):
        if not mensagem.embeds:
            continue

        embed = mensagem.embeds[0]
        meta = parse_meta(embed.footer.text if embed.footer else None)

        if meta.get("db") != "booster":
            continue

        if (
            user_id is not None
            and meta.get("user_id") != str(user_id)
        ):
            continue

        encontrados.append((mensagem, meta, embed))

    return encontrados
