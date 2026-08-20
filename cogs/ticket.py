import asyncio
import re
import unicodedata
from pathlib import Path

import discord
from discord.ext import commands

from utils.discord_db import (
    obter_proximo_ticket_id,
    registrar_ticket_aberto,
    registrar_ticket_fechado,
)
from utils.transcript import gerar_transcript


TICKETS_CATEGORY_ID = 1539818688138707044


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
                f"categoria:{categoria_escolhida}"
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

        dono_id = None
        ticket_id = None
        categoria = "desconhecida"

        if canal.topic:
            procura_dono = re.search(
                r"ticket_owner:(\d+)",
                canal.topic
            )

            procura_ticket = re.search(
                r"ticket_id:(\d+)",
                canal.topic
            )

            procura_categoria = re.search(
                r"categoria:([a-zA-Z0-9_-]+)",
                canal.topic
            )

            if procura_dono:
                dono_id = int(
                    procura_dono.group(1)
                )

            if procura_ticket:
                ticket_id = int(
                    procura_ticket.group(1)
                )

            if procura_categoria:
                categoria = procura_categoria.group(1)

        usuario = interaction.user

        eh_dono = (
            dono_id is not None
            and usuario.id == dono_id
        )

        eh_staff = (
            usuario.guild_permissions.administrator
            or usuario.guild_permissions.manage_messages
            or usuario.guild_permissions.manage_guild
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
                transcript
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
