import asyncio
import re
import unicodedata
from pathlib import Path

import discord
from discord.ext import commands

from utils.discord_db import (
    obter_proximo_ticket_id,
    parse_meta,
    registrar_avaliacao,
    registrar_falha_avaliacao,
    registrar_ticket_aberto,
    registrar_ticket_fechado,
)
from utils.transcript import gerar_transcript


TICKETS_CATEGORY_ID = 1539818688138707044

CARGOS_STAFF = {
    1085662246828511249,  # Direção
    1085662246828511248,  # Gerência
    1085662246828511247,  # Coordenação
    1085662246828511246,  # Supervisão
    1085662246828511242,  # Equipe Yoshi
}


CATEGORIAS_TICKET = {
    "duvida": {
        "nome": "Dúvida",
        "nome_canal": "duvida",
        "emoji": "❓",
        "descricao": "Tire uma dúvida com a staff",
        "precisa_resumo": True,
        "mensagem": (
            "Este espaço foi aberto para você tirar uma "
            "**dúvida com a nossa equipe**.\n\n"
            "O resumo informado antes da abertura do ticket "
            "está registrado abaixo. Se necessário, complemente "
            "com mais detalhes.\n\n"
            "📸 Você também pode enviar prints, links ou outras "
            "informações que possam ajudar a staff."
        )
    },

    "sorteio": {
        "nome": "Sorteio",
        "nome_canal": "sorteio",
        "emoji": "🥳",
        "descricao": "Assuntos relacionados a sorteios",
        "precisa_resumo": False,
        "mensagem": (
            "Este ticket é destinado a assuntos relacionados aos "
            "**sorteios do Yoshizinho City**.\n\n"
            "🎟️ Informe qual sorteio você está falando e explique "
            "sua dúvida ou problema.\n\n"
            "📸 Caso seja necessário, envie prints, comprovantes "
            "ou outras informações."
        )
    },

    "reportar": {
        "nome": "Reportar alguém",
        "nome_canal": "reportar",
        "emoji": "🚫",
        "descricao": "Reporte um usuário ou comportamento",
        "precisa_resumo": True,
        "mensagem": (
            "Este ticket foi aberto para analisar uma "
            "**denúncia ou comportamento inadequado**.\n\n"
            "O resumo inicial da denúncia está registrado abaixo.\n\n"
            "Para ajudar a staff na análise, envie também:\n"
            "👤 **Usuário envolvido**\n"
            "📸 **Prints, vídeos ou outras provas**\n"
            "🔗 **Links de mensagens, caso existam**\n\n"
            "⚠️ Denúncias falsas ou sem fundamento poderão "
            "ser desconsideradas."
        )
    },

    "criador": {
        "nome": "Tag criador",
        "nome_canal": "criador",
        "emoji": "▶️",
        "descricao": "Solicite acesso à tag Creator",
        "precisa_resumo": False,
        "mensagem": (
            "Este ticket é destinado à solicitação da **tag Creator**.\n\n"
            "Para que a staff possa analisar seu pedido, envie:\n"
            "🔗 **Link do seu canal ou perfil**\n"
            "🎮 **Tipo de conteúdo que você produz**\n"
            "📅 **Frequência das lives ou publicações**\n"
            "💬 **Uma breve apresentação do seu conteúdo**\n\n"
            "⚠️ A tag Creator não é concedida automaticamente."
        )
    }
}


def limpar_nome_usuario(usuario: discord.Member) -> str:
    nome = unicodedata.normalize(
        "NFKD",
        usuario.display_name
    )

    nome = (
        nome
        .encode("ascii", "ignore")
        .decode("ascii")
        .lower()
    )

    nome = re.sub(r"\s+", "-", nome)
    nome = re.sub(r"[^a-z0-9-]", "", nome)
    nome = re.sub(r"-+", "-", nome).strip("-")

    if not nome:
        nome = re.sub(
            r"[^a-z0-9-]",
            "",
            usuario.name.lower()
        )

    if not nome:
        nome = str(usuario.id)

    return nome[:25]


def encontrar_ticket_aberto(guild, usuario_id):
    for canal in guild.text_channels:
        if (
            canal.topic
            and f"ticket_owner:{usuario_id}" in canal.topic
        ):
            return canal

    return None


def eh_staff_ticket(membro: discord.Member) -> bool:
    if (
        membro.guild_permissions.administrator
        or membro.guild_permissions.manage_messages
        or membro.guild_permissions.manage_guild
    ):
        return True

    ids = {
        cargo.id
        for cargo in membro.roles
    }

    return bool(ids.intersection(CARGOS_STAFF))


def parse_ticket_topic(topic: str | None) -> dict:
    dados = {
        "ticket_id": None,
        "ticket_owner": None,
        "categoria": "desconhecida",
        "claimed_by": 0
    }

    if not topic:
        return dados

    padroes = {
        "ticket_id": r"ticket_id:(\d+)",
        "ticket_owner": r"ticket_owner:(\d+)",
        "categoria": r"categoria:([a-zA-Z0-9_-]+)",
        "claimed_by": r"claimed_by:(\d+)"
    }

    for chave, padrao in padroes.items():
        procura = re.search(
            padrao,
            topic
        )

        if not procura:
            continue

        valor = procura.group(1)

        if chave in {"ticket_id", "ticket_owner", "claimed_by"}:
            dados[chave] = int(valor)
        else:
            dados[chave] = valor

    return dados


def format_ticket_topic(dados: dict) -> str:
    return (
        f"ticket_id:{dados.get('ticket_id') or 0} | "
        f"ticket_owner:{dados.get('ticket_owner') or 0} | "
        f"categoria:{dados.get('categoria') or 'desconhecida'} | "
        f"claimed_by:{dados.get('claimed_by') or 0}"
    )


async def atualizar_topic_ticket(
    canal: discord.TextChannel,
    dados: dict,
    reason: str
):
    await canal.edit(
        topic=format_ticket_topic(
            dados
        ),
        reason=reason
    )


async def atualizar_embed_atendente(
    canal: discord.TextChannel,
    valor: str
):
    async for mensagem in canal.history(limit=20, oldest_first=True):
        if mensagem.author.bot and mensagem.embeds:
            embed = mensagem.embeds[0]

            for indice, campo in enumerate(embed.fields):
                if campo.name == "🙋 Atendido por":
                    embed.set_field_at(
                        indice,
                        name="🙋 Atendido por",
                        value=valor,
                        inline=False
                    )
                    break
            else:
                embed.add_field(
                    name="🙋 Atendido por",
                    value=valor,
                    inline=False
                )

            await mensagem.edit(embed=embed)
            return


class TicketRatingButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"ticket:rating:(?P<ticket_id>[0-9]+):(?P<stars>[1-5])"
):

    def __init__(
        self,
        ticket_id: int,
        stars: int
    ):
        self.ticket_id = ticket_id
        self.stars = stars

        super().__init__(
            discord.ui.Button(
                label="⭐" * stars,
                style=discord.ButtonStyle.secondary,
                custom_id=f"ticket:rating:{ticket_id}:{stars}"
            )
        )

    @classmethod
    async def from_custom_id(
        cls,
        interaction: discord.Interaction,
        item: discord.ui.Button,
        match
    ):
        return cls(
            int(match.group("ticket_id")),
            int(match.group("stars"))
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        if not interaction.message or not interaction.message.embeds:
            await interaction.response.send_message(
                "❌ Não consegui identificar esta avaliação.",
                ephemeral=True
            )
            return

        embed = interaction.message.embeds[0]
        meta = parse_meta(embed.footer.text if embed.footer else None)

        if meta.get("rated") == "1":
            await interaction.response.send_message(
                "⚠️ Este ticket já foi avaliado.",
                ephemeral=True
            )
            return

        owner_id = int(meta.get("owner_id", "0"))
        staff_id = int(meta.get("staff_id", "0"))

        if owner_id and interaction.user.id != owner_id:
            await interaction.response.send_message(
                "❌ Apenas o dono do ticket pode avaliar este atendimento.",
                ephemeral=True
            )
            return

        await registrar_avaliacao(
            interaction.client,
            self.ticket_id,
            owner_id or interaction.user.id,
            staff_id,
            self.stars
        )

        estrelas = "⭐" * self.stars

        novo_embed = discord.Embed(
            title="✅ Obrigado pela avaliação!",
            description=(
                "Sua nota:\n"
                f"{estrelas}\n\n"
                f"`{self.stars}/5`"
            ),
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )

        novo_embed.set_footer(
            text=(
                f"ticket_id={self.ticket_id};"
                f"owner_id={owner_id or interaction.user.id};"
                f"staff_id={staff_id};"
                "rated=1"
            )
        )

        await interaction.response.edit_message(
            embed=novo_embed,
            view=None
        )


class TicketRatingView(discord.ui.View):

    def __init__(
        self,
        ticket_id: int
    ):
        super().__init__(
            timeout=None
        )

        for estrelas in range(1, 6):
            self.add_item(
                TicketRatingButton(
                    ticket_id,
                    estrelas
                )
            )


async def criar_ticket(
    interaction: discord.Interaction,
    categoria_escolhida: str,
    resumo: str | None = None
):
    guild = interaction.guild
    usuario = interaction.user

    if guild is None:
        return

    if not interaction.response.is_done():
        await interaction.response.defer(
            ephemeral=True
        )

    ticket_existente = encontrar_ticket_aberto(
        guild,
        usuario.id
    )

    if ticket_existente:
        await interaction.followup.send(
            f"⚠️ Você já possui um ticket aberto: "
            f"{ticket_existente.mention}",
            ephemeral=True
        )
        return

    dados = CATEGORIAS_TICKET[
        categoria_escolhida
    ]

    categoria_discord = guild.get_channel(
        TICKETS_CATEGORY_ID
    )

    if not isinstance(
        categoria_discord,
        discord.CategoryChannel
    ):
        await interaction.followup.send(
            "❌ A categoria **Tickets** não foi encontrada.",
            ephemeral=True
        )
        return

    try:
        ticket_id = await obter_proximo_ticket_id(
            interaction.client
        )
    except Exception as erro:
        print(
            f"❌ Não consegui obter o número do ticket: {erro}"
        )

        await interaction.followup.send(
            "❌ Não consegui acessar o sistema de registros "
            "dos tickets.",
            ephemeral=True
        )
        return

    overwrites = {
        guild.default_role:
            discord.PermissionOverwrite(
                view_channel=False
            ),

        usuario:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            ),

        guild.me:
            discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True,
                attach_files=True,
                embed_links=True
            )
    }

    for cargo in guild.roles:
        if (
            cargo.permissions.administrator
            or cargo.permissions.manage_messages
            or cargo.permissions.manage_guild
        ):
            overwrites[cargo] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )
            )

    nome_usuario = limpar_nome_usuario(
        usuario
    )

    nome_canal = (
        f"{dados['nome_canal']}-{nome_usuario}"
    )

    try:
        canal_ticket = await guild.create_text_channel(
            name=nome_canal,
            category=categoria_discord,
            overwrites=overwrites,
            topic=(
                f"ticket_id:{ticket_id} | "
                f"ticket_owner:{usuario.id} | "
                f"categoria:{categoria_escolhida} | "
                "claimed_by:0"
            ),
            reason=(
                f"Ticket #{ticket_id} - "
                f"{dados['nome']} aberto por "
                f"{usuario} ({usuario.id})"
            )
        )

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ Não consegui criar o ticket. "
            "Verifique a permissão **Gerenciar Canais**.",
            ephemeral=True
        )
        return

    except discord.HTTPException as erro:
        print(f"❌ Erro ao criar ticket: {erro}")

        await interaction.followup.send(
            "❌ O Discord retornou um erro ao criar o ticket.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=(
            f"{dados['emoji']} "
            f"Ticket #{ticket_id} • {dados['nome']}"
        ),
        description=(
            f"Olá {usuario.mention}! 👋\n\n"
            f"{dados['mensagem']}"
        ),
        color=discord.Color.from_rgb(
            0,
            170,
            255
        ),
        timestamp=discord.utils.utcnow()
    )

    embed.add_field(
        name="🎫 Ticket",
        value=f"`#{ticket_id}`",
        inline=True
    )

    embed.add_field(
        name="📂 Categoria",
        value=f"**{dados['nome']}**",
        inline=True
    )

    embed.add_field(
        name="👤 Solicitante",
        value=usuario.mention,
        inline=True
    )

    if resumo:
        embed.add_field(
            name="📝 Resumo do problema",
            value=resumo,
            inline=False
        )

    embed.add_field(
        name="🆔 ID do usuário",
        value=f"`{usuario.id}`",
        inline=False
    )

    embed.add_field(
        name="🔔 Atendimento",
        value=(
            "Aguarde uma resposta da staff. "
            "Quando o atendimento terminar, utilize "
            "o botão **Fechar ticket**."
        ),
        inline=False
    )

    embed.add_field(
        name="🙋 Atendido por",
        value="Aguardando atendimento",
        inline=False
    )

    embed.set_thumbnail(
        url=usuario.display_avatar.url
    )

    embed.set_footer(
        text="Yoshizinho City • Central de Atendimento"
    )

    await canal_ticket.send(
        content=usuario.mention,
        embed=embed,
        view=FecharTicketView()
    )

    try:
        await registrar_ticket_aberto(
            interaction.client,
            ticket_id,
            usuario,
            canal_ticket,
            dados["nome"],
            categoria_escolhida,
            resumo
        )
    except Exception as erro:
        print(
            f"❌ Ticket criado, mas falhou ao registrar o log: {erro}"
        )

    await interaction.followup.send(
        f"✅ Seu **Ticket #{ticket_id}** de "
        f"**{dados['nome']}** foi criado: "
        f"{canal_ticket.mention}",
        ephemeral=True
    )


async def solicitar_avaliacao_ticket(
    bot,
    dono: discord.Member,
    ticket_id: int,
    atendente_id: int,
    atendente: discord.Member | None = None
):
    atendente_texto = (
        atendente.mention
        if atendente is not None
        else (
            f"<@{atendente_id}>"
            if atendente_id
            else "Não registrado"
        )
    )

    embed = discord.Embed(
        title="⭐ Como foi seu atendimento?",
        description=(
            f"Seu **Ticket #{ticket_id}** foi encerrado.\n\n"
            "**Atendido por:**\n"
            f"{atendente_texto}\n\n"
            "Avalie sua experiência:"
        ),
        color=discord.Color.gold(),
        timestamp=discord.utils.utcnow()
    )

    embed.set_footer(
        text=(
            f"ticket_id={ticket_id};"
            f"owner_id={dono.id};"
            f"staff_id={atendente_id or 0};"
            "rated=0"
        )
    )

    try:
        await dono.send(
            embed=embed,
            view=TicketRatingView(
                ticket_id
            )
        )

    except (discord.Forbidden, discord.HTTPException):
        await registrar_falha_avaliacao(
            bot,
            ticket_id,
            dono.id,
            "DMs fechadas."
        )


class ResumoTicketModal(discord.ui.Modal):

    def __init__(
        self,
        categoria_escolhida
    ):
        self.categoria_escolhida = categoria_escolhida

        dados = CATEGORIAS_TICKET[
            categoria_escolhida
        ]

        super().__init__(
            title=(
                f"{dados['emoji']} "
                f"{dados['nome']}"
            )
        )

        if categoria_escolhida == "duvida":
            label = "Qual é a sua dúvida?"
            placeholder = (
                "Ex.: Estou com dúvida sobre como funciona "
                "o sistema de cargos..."
            )

        elif categoria_escolhida == "reportar":
            label = "Resuma o ocorrido"
            placeholder = (
                "Ex.: O usuário está enviando spam e "
                "ofendendo outros membros..."
            )

        else:
            label = "Resumo"
            placeholder = (
                "Explique brevemente o motivo do ticket..."
            )

        self.resumo = discord.ui.TextInput(
            label=label,
            placeholder=placeholder,
            style=discord.TextStyle.paragraph,
            min_length=10,
            max_length=800,
            required=True
        )

        self.add_item(
            self.resumo
        )

    async def on_submit(
        self,
        interaction: discord.Interaction
    ):
        await criar_ticket(
            interaction,
            self.categoria_escolhida,
            str(self.resumo.value)
        )


class FecharTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="Assumir ticket",
        emoji="🙋",
        style=discord.ButtonStyle.primary,
        custom_id="yoshi:ticket:assumir"
    )
    async def assumir_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
            return

        if not isinstance(interaction.user, discord.Member):
            return

        dados = parse_ticket_topic(canal.topic)

        dono_id = dados.get("ticket_owner")
        claimed_by = dados.get("claimed_by") or 0

        if not eh_staff_ticket(interaction.user):
            await interaction.response.send_message(
                "❌ Apenas a staff pode assumir tickets.",
                ephemeral=True
            )
            return

        if dono_id and interaction.user.id == dono_id:
            await interaction.response.send_message(
                "❌ O dono do ticket não pode assumir o próprio atendimento.",
                ephemeral=True
            )
            return

        if claimed_by:
            await interaction.response.send_message(
                f"⚠️ Este ticket já está sendo atendido por <@{claimed_by}>.",
                ephemeral=True
            )
            return

        dados["claimed_by"] = interaction.user.id

        try:
            await atualizar_topic_ticket(
                canal,
                dados,
                f"Ticket assumido por {interaction.user} ({interaction.user.id})"
            )

            await atualizar_embed_atendente(
                canal,
                interaction.user.mention
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não tenho permissão para atualizar este ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "✅ Você assumiu este ticket.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Liberar ticket",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        custom_id="yoshi:ticket:liberar"
    )
    async def liberar_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
            return

        if not isinstance(interaction.user, discord.Member):
            return

        dados = parse_ticket_topic(canal.topic)
        claimed_by = dados.get("claimed_by") or 0

        if not claimed_by:
            await interaction.response.send_message(
                "⚠️ Este ticket ainda não foi assumido.",
                ephemeral=True
            )
            return

        pode_liberar = (
            interaction.user.id == claimed_by
            or interaction.user.guild_permissions.administrator
            or interaction.user.guild_permissions.manage_guild
        )

        if not pode_liberar:
            await interaction.response.send_message(
                "❌ Apenas quem assumiu ou a administração pode liberar este ticket.",
                ephemeral=True
            )
            return

        dados["claimed_by"] = 0

        try:
            await atualizar_topic_ticket(
                canal,
                dados,
                f"Ticket liberado por {interaction.user} ({interaction.user.id})"
            )

            await atualizar_embed_atendente(
                canal,
                "Aguardando atendimento"
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não tenho permissão para atualizar este ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "✅ Ticket liberado para outro membro da staff assumir.",
            ephemeral=True
        )

    @discord.ui.button(
        label="Fechar ticket",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="yoshi:ticket:fechar"
    )
    async def fechar_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        canal = interaction.channel

        if not isinstance(
            canal,
            discord.TextChannel
        ):
            return

        dados_ticket = parse_ticket_topic(
            canal.topic
        )

        dono_id = dados_ticket.get(
            "ticket_owner"
        )

        ticket_id = dados_ticket.get(
            "ticket_id"
        )

        categoria = dados_ticket.get(
            "categoria",
            "desconhecida"
        )

        atendente_id = dados_ticket.get(
            "claimed_by"
        ) or 0

        usuario = interaction.user

        eh_dono = (
            dono_id is not None
            and usuario.id == dono_id
        )

        eh_staff = (
            isinstance(usuario, discord.Member)
            and eh_staff_ticket(usuario)
        )

        if not eh_dono and not eh_staff:
            await interaction.response.send_message(
                "❌ Você não possui permissão para fechar este ticket.",
                ephemeral=True
            )
            return

        if ticket_id is None or dono_id is None:
            await interaction.response.send_message(
                "❌ Não consegui identificar os dados deste ticket.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Gerando transcript e fechando o ticket "
            "em **5 segundos**..."
        )

        await asyncio.sleep(5)

        guild = canal.guild

        dono = guild.get_member(
            dono_id
        )

        if dono is None:
            try:
                dono = await guild.fetch_member(
                    dono_id
                )
            except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                dono = None

        atendente = (
            guild.get_member(
                atendente_id
            )
            if atendente_id
            else None
        )

        try:
            transcript = await gerar_transcript(
                canal
            )

            await registrar_ticket_fechado(
                interaction.client,
                ticket_id,
                dono_id,
                usuario,
                canal.name,
                categoria,
                transcript,
                atendente_id,
                atendente
            )

        except Exception as erro:
            print(
                f"❌ Falha ao registrar o fechamento do ticket "
                f"#{ticket_id}: {erro}"
            )

            try:
                await canal.send(
                    "❌ **O ticket não foi apagado.** "
                    "Não consegui salvar o transcript/log de fechamento."
                )
            except discord.HTTPException:
                pass

            return

        try:
            await canal.delete(
                reason=(
                    f"Ticket #{ticket_id} fechado por "
                    f"{usuario} ({usuario.id})"
                )
            )

        except discord.Forbidden:
            print(
                "❌ Não tenho permissão para excluir o ticket."
            )

        except discord.HTTPException as erro:
            print(
                f"❌ Erro ao fechar ticket: {erro}"
            )

        if dono is not None:
            await solicitar_avaliacao_ticket(
                interaction.client,
                dono,
                ticket_id,
                atendente_id,
                atendente
            )
        else:
            try:
                await registrar_falha_avaliacao(
                    interaction.client,
                    ticket_id,
                    dono_id,
                    "Usuário não encontrado para envio da DM."
                )
            except Exception as erro:
                print(
                    f"❌ Falha ao registrar ausência de avaliação: {erro}"
                )


class TicketSelect(discord.ui.Select):

    def __init__(self):
        opcoes = [
            discord.SelectOption(
                label="Dúvida",
                value="duvida",
                emoji="❓",
                description="Tire uma dúvida com a staff"
            ),

            discord.SelectOption(
                label="Sorteio",
                value="sorteio",
                emoji="🥳",
                description="Assuntos relacionados a sorteios"
            ),

            discord.SelectOption(
                label="Reportar alguém",
                value="reportar",
                emoji="🚫",
                description="Reporte um usuário ou comportamento"
            ),

            discord.SelectOption(
                label="Tag criador",
                value="criador",
                emoji="▶️",
                description="Solicite acesso à tag Creator"
            )
        ]

        super().__init__(
            placeholder="Selecione uma opção",
            min_values=1,
            max_values=1,
            options=opcoes,
            custom_id="yoshi:ticket:categoria"
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        guild = interaction.guild
        usuario = interaction.user

        if guild is None:
            return

        ticket_existente = encontrar_ticket_aberto(
            guild,
            usuario.id
        )

        if ticket_existente:
            await interaction.response.send_message(
                f"⚠️ Você já possui um ticket aberto: "
                f"{ticket_existente.mention}",
                ephemeral=True
            )
            return

        categoria_escolhida = self.values[0]

        dados = CATEGORIAS_TICKET[
            categoria_escolhida
        ]

        if dados["precisa_resumo"]:
            await interaction.response.send_modal(
                ResumoTicketModal(
                    categoria_escolhida
                )
            )
            return

        await criar_ticket(
            interaction,
            categoria_escolhida
        )


class TicketView(discord.ui.View):

    def __init__(self):
        super().__init__(
            timeout=None
        )

        self.add_item(
            TicketSelect()
        )


class Ticket(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_dynamic_items(
            TicketRatingButton
        )

        self.bot.add_view(
            TicketView()
        )

        self.bot.add_view(
            FecharTicketView()
        )

    @commands.command(
        name="ticket"
    )
    @commands.has_permissions(
        manage_guild=True
    )
    async def ticket(
        self,
        ctx
    ):
        embed = discord.Embed(
            title="🎟️ Central de Atendimento",
            description=(
                "Para que possamos ajudar você da melhor forma possível, "
                "escolha abaixo a categoria que mais se encaixa na sua necessidade.\n\n"
                "**🕐 Horário de Atendimento**\n\n"
                "Segunda a Domingo: **08:00 às 22:00** "
                "(Horário de Brasília)\n\n"
                "Exceto em feriados nacionais.\n\n"
                "**📌 Observações:**\n\n"
                "Atendimentos fora do horário podem ocorrer, "
                "mas não são garantidos.\n\n"
                "Escolha a categoria correta para um atendimento "
                "mais rápido e eficiente.\n\n"
                "Tickets abertos em categorias incorretas poderão "
                "ser encerrados sem aviso prévio.\n\n"
                "Nossa equipe está pronta para ajudar você. "
                "Abra seu ticket e aguarde o atendimento! 😊"
            ),
            color=discord.Color.red()
        )

        caminho_gif = (
            Path(__file__).resolve().parent.parent
            / "img"
            / "yoshi_overlay_fade.gif"
        )

        gif = None

        if caminho_gif.exists():
            gif = discord.File(
                caminho_gif,
                filename="yoshi_overlay_fade.gif"
            )

            embed.set_image(
                url="attachment://yoshi_overlay_fade.gif"
            )

        embed.set_footer(
            text="Yoshi • Central de Atendimento"
        )

        try:
            await ctx.message.delete()

        except discord.Forbidden:
            pass

        if gif is not None:
            await ctx.send(
                embed=embed,
                file=gif,
                view=TicketView()
            )

        else:
            await ctx.send(
                embed=embed,
                view=TicketView()
            )


async def setup(bot):
    await bot.add_cog(
        Ticket(bot)
    )
