import discord
from discord.ext import commands

from utils.discord_db import (
    embed_field,
    listar_avaliacoes,
    listar_boosters,
    listar_infracoes,
    listar_logs_tickets,
)


CARGOS_ADMIN = {
    1085662246828511249,  # Direção
    1085662246828511248,  # Gerência
    1085662246828511247,  # Coordenação
    1085662246828511246,  # Supervisão
    1085662246828511242,  # Equipe Yoshi
}


def eh_staff():
    async def predicate(ctx):
        if not isinstance(ctx.author, discord.Member):
            return False

        if (
            ctx.author.guild_permissions.administrator
            or ctx.author.guild_permissions.manage_guild
            or ctx.author.guild_permissions.manage_messages
        ):
            return True

        ids = {
            cargo.id
            for cargo in ctx.author.roles
        }

        return bool(
            ids.intersection(
                CARGOS_ADMIN
            )
        )

    return commands.check(
        predicate
    )


class Consultas(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="ticketinfo"
    )
    @eh_staff()
    async def ticketinfo(
        self,
        ctx,
        ticket_id: int
    ):
        async with ctx.typing():
            logs = await listar_logs_tickets(
                self.bot,
                ticket_id=ticket_id
            )

        if not logs:
            await ctx.send(
                f"❌ Não encontrei o **Ticket #{ticket_id}**."
            )
            return

        aberto = None
        fechado = None

        for mensagem, meta, embed in logs:
            if meta.get("status") == "aberto":
                aberto = (
                    mensagem,
                    meta,
                    embed
                )

            elif meta.get("status") == "fechado":
                fechado = (
                    mensagem,
                    meta,
                    embed
                )

        base = aberto or fechado

        _, meta, embed_log = base

        embed = discord.Embed(
            title=f"🎫 Ticket #{ticket_id}",
            color=discord.Color.from_rgb(
                0,
                170,
                255
            ),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="👤 Usuário",
            value=embed_field(
                embed_log,
                "👤 Usuário",
                embed_field(
                    embed_log,
                    "👤 Dono do ticket"
                )
            ),
            inline=True
        )

        embed.add_field(
            name="📂 Categoria",
            value=meta.get(
                "categoria",
                "—"
            ),
            inline=True
        )

        embed.add_field(
            name="📊 Status",
            value=(
                "🔒 Fechado"
                if fechado
                else "🟢 Aberto"
            ),
            inline=True
        )

        if aberto:
            embed_aberto = aberto[2]

            embed.add_field(
                name="📝 Resumo",
                value=embed_field(
                    embed_aberto,
                    "📝 Resumo"
                ),
                inline=False
            )

            embed.add_field(
                name="📍 Canal original",
                value=embed_field(
                    embed_aberto,
                    "📍 Canal"
                ),
                inline=False
            )

        if fechado:
            embed_fechado = fechado[2]

            embed.add_field(
                name="🔨 Fechado por",
                value=embed_field(
                    embed_fechado,
                    "🔨 Fechado por"
                ),
                inline=False
            )

        embed.set_footer(
            text="Yoshizinho City • Histórico de Tickets"
        )

        await ctx.send(
            embed=embed
        )

    @commands.command(
        name="tickets"
    )
    @eh_staff()
    async def tickets(
        self,
        ctx,
        membro: discord.Member
    ):
        async with ctx.typing():
            logs = await listar_logs_tickets(
                self.bot,
                owner_id=membro.id
            )

        if not logs:
            await ctx.send(
                f"📭 {membro.mention} não possui tickets registrados."
            )
            return

        tickets = {}

        for mensagem, meta, embed in logs:
            ticket_id = int(
                meta.get(
                    "ticket_id",
                    "0"
                )
            )

            if not ticket_id:
                continue

            dados = tickets.setdefault(
                ticket_id,
                {
                    "status": "aberto",
                    "categoria": meta.get(
                        "categoria",
                        "—"
                    ),
                    "data": mensagem.created_at
                }
            )

            if meta.get("status") == "fechado":
                dados["status"] = "fechado"

        ordenados = sorted(
            tickets.items(),
            key=lambda item: item[0],
            reverse=True
        )

        linhas = []

        for ticket_id, dados in ordenados[:20]:
            status = (
                "🔒"
                if dados["status"] == "fechado"
                else "🟢"
            )

            data = dados["data"].strftime(
                "%d/%m/%Y"
            )

            linhas.append(
                f"{status} **#{ticket_id}** • "
                f"{dados['categoria']} • {data}"
            )

        embed = discord.Embed(
            title=f"🎫 Tickets de {membro.display_name}",
            description="\n".join(linhas),
            color=discord.Color.from_rgb(
                0,
                170,
                255
            )
        )

        embed.add_field(
            name="Total registrado",
            value=str(
                len(tickets)
            ),
            inline=False
        )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        await ctx.send(
            embed=embed
        )

    @commands.command(
        name="infracoes"
    )
    @eh_staff()
    async def infracoes(
        self,
        ctx,
        membro: discord.Member
    ):
        async with ctx.typing():
            registros = await listar_infracoes(
                self.bot,
                membro.id
            )

        if not registros:
            await ctx.send(
                f"✅ {membro.mention} não possui infrações registradas."
            )
            return

        ultimas = registros[-10:]

        linhas = []

        for mensagem, meta, embed_log in reversed(
            ultimas
        ):
            data = mensagem.created_at.strftime(
                "%d/%m/%Y %H:%M"
            )

            motivo = embed_field(
                embed_log,
                "⚠️ Motivo"
            )

            acao = embed_field(
                embed_log,
                "🔨 Ação"
            )

            linhas.append(
                f"**{data}**\n"
                f"• {motivo}\n"
                f"• {acao}"
            )

        embed = discord.Embed(
            title=f"🚨 Infrações de {membro.display_name}",
            description="\n\n".join(
                linhas
            ),
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Total registrado",
            value=str(
                len(registros)
            ),
            inline=False
        )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        await ctx.send(
            embed=embed
        )

    @commands.command(
        name="historico"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    @eh_staff()
    async def historico(
        self,
        ctx,
        membro: discord.Member
    ):
        async with ctx.typing():
            tickets_logs = await listar_logs_tickets(
                self.bot,
                owner_id=membro.id
            )

            infracoes_logs = await listar_infracoes(
                self.bot,
                membro.id
            )

            booster_logs = await listar_boosters(
                self.bot,
                membro.id
            )

        tickets_ids = {
            meta.get("ticket_id")
            for _, meta, _ in tickets_logs
            if meta.get("ticket_id")
        }

        ultimo_booster = (
            booster_logs[-1][1].get(
                "evento"
            )
            if booster_logs
            else None
        )

        embed = discord.Embed(
            title=f"📋 Histórico de {membro.display_name}",
            color=discord.Color.from_rgb(
                0,
                170,
                255
            ),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="👤 Usuário",
            value=f"{membro.mention}\n`{membro.id}`",
            inline=False
        )

        embed.add_field(
            name="🎫 Tickets",
            value=str(
                len(tickets_ids)
            ),
            inline=True
        )

        embed.add_field(
            name="🚨 Infrações",
            value=str(
                len(infracoes_logs)
            ),
            inline=True
        )

        embed.add_field(
            name="💜 Booster atual",
            value=(
                "✅ Sim"
                if membro.premium_since
                else "❌ Não"
            ),
            inline=True
        )

        if ultimo_booster:
            embed.add_field(
                name="💜 Último registro de boost",
                value=ultimo_booster,
                inline=False
            )

        embed.add_field(
            name="📅 Conta criada",
            value=discord.utils.format_dt(
                membro.created_at,
                style="f"
            ),
            inline=False
        )

        if membro.joined_at:
            embed.add_field(
                name="📥 Entrou no servidor",
                value=discord.utils.format_dt(
                    membro.joined_at,
                    style="f"
                ),
                inline=False
            )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        await ctx.send(
            embed=embed
        )

    @commands.command(
        name="stats"
    )
    @commands.cooldown(1, 15, commands.BucketType.user)
    @eh_staff()
    async def stats(
        self,
        ctx
    ):
        async with ctx.typing():
            ticket_logs = await listar_logs_tickets(
                self.bot
            )

            infracoes_logs = await listar_infracoes(
                self.bot
            )

            avaliacoes_logs = await listar_avaliacoes(
                self.bot
            )

        tickets_abertos_log = {
            meta.get("ticket_id")
            for _, meta, _ in ticket_logs
            if (
                meta.get("ticket_id")
                and meta.get("status") == "aberto"
            )
        }

        tickets_fechados = {
            meta.get("ticket_id")
            for _, meta, _ in ticket_logs
            if (
                meta.get("ticket_id")
                and meta.get("status") == "fechado"
            )
        }

        tickets_total = len(
            tickets_abertos_log
        )

        tickets_abertos_agora = sum(
            1
            for canal in ctx.guild.text_channels
            if (
                canal.topic
                and "ticket_owner:" in canal.topic
            )
        )

        boosters_atuais = sum(
            1
            for membro in ctx.guild.members
            if membro.premium_since is not None
        )

        youtube = self.bot.get_cog(
            "Youtube"
        )

        youtube_status = "❌ Offline"

        if youtube is not None:
            loop = getattr(
                youtube,
                "verificar_youtube",
                None
            )

            if (
                loop is not None
                and loop.is_running()
            ):
                youtube_status = "✅ Funcionando"

        ping = round(
            self.bot.latency * 1000
        )

        notas = []

        for _, meta, _ in avaliacoes_logs:
            try:
                notas.append(
                    int(
                        meta.get(
                            "rating",
                            "0"
                        )
                    )
                )
            except ValueError:
                continue

        media_avaliacoes = (
            sum(notas) / len(notas)
            if notas
            else 0
        )

        embed = discord.Embed(
            title="📊 Estatísticas do Yoshizinho City",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="🎫 Tickets criados",
            value=str(
                tickets_total
            ),
            inline=True
        )

        embed.add_field(
            name="🟢 Tickets abertos",
            value=str(
                tickets_abertos_agora
            ),
            inline=True
        )

        embed.add_field(
            name="🔒 Tickets fechados",
            value=str(
                len(tickets_fechados)
            ),
            inline=True
        )

        embed.add_field(
            name="🚨 Infrações",
            value=str(
                len(infracoes_logs)
            ),
            inline=True
        )

        embed.add_field(
            name="💜 Boosters atuais",
            value=str(
                boosters_atuais
            ),
            inline=True
        )

        embed.add_field(
            name="👥 Membros",
            value=str(
                ctx.guild.member_count
            ),
            inline=True
        )

        embed.add_field(
            name="📡 Ping",
            value=f"{ping} ms",
            inline=True
        )

        embed.add_field(
            name="▶️ YouTube",
            value=youtube_status,
            inline=True
        )

        embed.add_field(
            name="⭐ Avaliações",
            value=str(
                len(notas)
            ),
            inline=True
        )

        embed.add_field(
            name="⭐ Média",
            value=(
                f"{media_avaliacoes:.1f} / 5"
                if notas
                else "Sem avaliações"
            ),
            inline=True
        )

        embed.add_field(
            name="🧩 Cogs",
            value=str(
                len(self.bot.cogs)
            ),
            inline=True
        )

        embed.set_footer(
            text="Yoshizinho City • Estatísticas"
        )

        await ctx.send(
            embed=embed
        )

    @commands.command(
        name="avaliacoes"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    @eh_staff()
    async def avaliacoes(
        self,
        ctx,
        membro: discord.Member
    ):
        async with ctx.typing():
            registros = await listar_avaliacoes(
                self.bot,
                staff_id=membro.id
            )

        notas = []

        for _, meta, _ in registros:
            try:
                notas.append(
                    int(
                        meta.get(
                            "rating",
                            "0"
                        )
                    )
                )
            except ValueError:
                continue

        contagem = {
            estrela: notas.count(estrela)
            for estrela in range(1, 6)
        }

        media = (
            sum(notas) / len(notas)
            if notas
            else 0
        )

        embed = discord.Embed(
            title=f"⭐ Avaliações de {membro.display_name}",
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="Atendimentos avaliados",
            value=str(len(notas)),
            inline=True
        )

        embed.add_field(
            name="Média",
            value=(
                f"{media:.1f}/5"
                if notas
                else "Sem avaliações"
            ),
            inline=True
        )

        embed.add_field(
            name="Distribuição",
            value=(
                f"5⭐: {contagem[5]}\n"
                f"4⭐: {contagem[4]}\n"
                f"3⭐: {contagem[3]}\n"
                f"2⭐: {contagem[2]}\n"
                f"1⭐: {contagem[1]}"
            ),
            inline=False
        )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        await ctx.send(
            embed=embed
        )

    @commands.command(
        name="userinfo"
    )
    @commands.cooldown(1, 10, commands.BucketType.user)
    @eh_staff()
    async def userinfo(
        self,
        ctx,
        membro: discord.Member
    ):
        async with ctx.typing():
            tickets_logs = await listar_logs_tickets(
                self.bot,
                owner_id=membro.id
            )

            infracoes_logs = await listar_infracoes(
                self.bot,
                membro.id
            )

            avaliacoes_logs = await listar_avaliacoes(
                self.bot,
                staff_id=membro.id
            )

        tickets_ids = {
            meta.get("ticket_id")
            for _, meta, _ in tickets_logs
            if meta.get("ticket_id")
        }

        notas = []

        for _, meta, _ in avaliacoes_logs:
            try:
                notas.append(int(meta.get("rating", "0")))
            except ValueError:
                continue

        cargos = [
            cargo.mention
            for cargo in membro.roles
            if not cargo.is_default()
        ]

        embed = discord.Embed(
            title=f"👤 Informações de {membro.display_name}",
            color=discord.Color.from_rgb(0, 170, 255),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="Usuário",
            value=f"{membro.mention}\n`{membro}`",
            inline=True
        )

        embed.add_field(
            name="ID",
            value=f"`{membro.id}`",
            inline=True
        )

        embed.add_field(
            name="Conta criada",
            value=discord.utils.format_dt(membro.created_at, style="f"),
            inline=False
        )

        if membro.joined_at:
            embed.add_field(
                name="Entrou no servidor",
                value=discord.utils.format_dt(membro.joined_at, style="f"),
                inline=False
            )

        embed.add_field(
            name="Cargos",
            value=", ".join(cargos[:20]) if cargos else "Nenhum cargo.",
            inline=False
        )

        embed.add_field(
            name="Booster",
            value="Sim" if membro.premium_since else "Não",
            inline=True
        )

        embed.add_field(
            name="Tickets registrados",
            value=str(len(tickets_ids)),
            inline=True
        )

        embed.add_field(
            name="Infrações",
            value=str(len(infracoes_logs)),
            inline=True
        )

        if notas:
            embed.add_field(
                name="⭐ Avaliações recebidas",
                value=(
                    f"{len(notas)} avaliação(ões)\n"
                    f"Média: {sum(notas) / len(notas):.1f}/5"
                ),
                inline=False
            )

        embed.set_thumbnail(
            url=membro.display_avatar.url
        )

        await ctx.send(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(
        Consultas(bot)
    )
