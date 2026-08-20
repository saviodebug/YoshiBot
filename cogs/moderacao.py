import re
from datetime import timedelta

import discord
from discord.ext import commands

from utils.discord_db import registrar_infracao


CARGOS_STAFF = {
    1085662246828511249,  # Direção
    1085662246828511248,  # Gerência
    1085662246828511247,  # Coordenação
    1085662246828511246,  # Supervisão
    1085662246828511242,  # Equipe Yoshi
}

UNIDADES_TIMEOUT = {
    "s": 1,
    "m": 60,
    "h": 60 * 60,
    "d": 60 * 60 * 24,
}

MAX_TIMEOUT = timedelta(days=28)


def eh_staff_com(permissao: str | None = None):
    async def predicate(ctx):
        if not isinstance(ctx.author, discord.Member):
            return False

        perms = ctx.author.guild_permissions

        if perms.administrator or perms.manage_guild:
            return True

        if permissao and getattr(perms, permissao, False):
            return True

        ids = {
            cargo.id
            for cargo in ctx.author.roles
        }

        return bool(ids.intersection(CARGOS_STAFF))

    return commands.check(predicate)


def parse_duracao(valor: str) -> timedelta:
    match = re.fullmatch(r"(\d+)([smhd])", valor.lower().strip())

    if match is None:
        raise commands.BadArgument("Duração inválida.")

    quantidade = int(match.group(1))
    unidade = match.group(2)

    if quantidade <= 0:
        raise commands.BadArgument("Duração inválida.")

    duracao = timedelta(seconds=quantidade * UNIDADES_TIMEOUT[unidade])

    if duracao > MAX_TIMEOUT:
        raise commands.BadArgument("Timeout acima do limite do Discord.")

    return duracao


class Moderacao(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def _validar_alvo(
        self,
        ctx,
        membro: discord.Member,
        acao: str
    ) -> str | None:
        if membro.id == self.bot.user.id:
            return f"❌ Não posso {acao} o próprio bot."

        if membro.id == ctx.author.id:
            return f"❌ Você não pode {acao} a si mesmo."

        if ctx.guild.owner_id != ctx.author.id:
            if membro.top_role >= ctx.author.top_role:
                return "❌ Esse usuário está acima ou no mesmo nível que você."

        bot_member = ctx.guild.me

        if bot_member is None or membro.top_role >= bot_member.top_role:
            return "❌ Esse usuário está acima ou no mesmo nível que o bot."

        return None

    async def _enviar_dm(
        self,
        membro: discord.Member,
        titulo: str,
        motivo: str,
        responsavel: discord.Member
    ) -> bool:
        embed = discord.Embed(
            title=titulo,
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="Motivo",
            value=motivo,
            inline=False
        )

        embed.add_field(
            name="Responsável",
            value=f"{responsavel} (`{responsavel.id}`)",
            inline=False
        )

        try:
            await membro.send(embed=embed)
            return True
        except (discord.Forbidden, discord.HTTPException):
            return False

    async def _registrar(
        self,
        ctx,
        membro: discord.Member,
        motivo: str,
        tipo: str,
        acao: str
    ):
        await registrar_infracao(
            self.bot,
            membro,
            motivo,
            tipo,
            acao,
            ctx.channel,
            origem="manual",
            moderador=ctx.author
        )

    @commands.command(name="ban")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @eh_staff_com("ban_members")
    async def ban(
        self,
        ctx,
        membro: discord.Member,
        *,
        motivo: str
    ):
        erro = self._validar_alvo(ctx, membro, "banir")

        if erro:
            await ctx.send(erro, delete_after=8)
            return

        await self._enviar_dm(
            membro,
            "🚫 Você foi banido do Yoshizinho City",
            motivo,
            ctx.author
        )

        await membro.ban(
            reason=f"{motivo} | Responsável: {ctx.author} ({ctx.author.id})"
        )

        await self._registrar(ctx, membro, motivo, "ban_manual", "Banido do servidor")
        await ctx.send(f"✅ {membro} foi banido.")

    @commands.command(name="kick")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @eh_staff_com("kick_members")
    async def kick(
        self,
        ctx,
        membro: discord.Member,
        *,
        motivo: str
    ):
        erro = self._validar_alvo(ctx, membro, "expulsar")

        if erro:
            await ctx.send(erro, delete_after=8)
            return

        await self._enviar_dm(
            membro,
            "👢 Você foi expulso do Yoshizinho City",
            motivo,
            ctx.author
        )

        await membro.kick(
            reason=f"{motivo} | Responsável: {ctx.author} ({ctx.author.id})"
        )

        await self._registrar(ctx, membro, motivo, "kick_manual", "Expulso do servidor")
        await ctx.send(f"✅ {membro} foi expulso.")

    @commands.command(name="timeout")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @eh_staff_com("moderate_members")
    async def timeout(
        self,
        ctx,
        membro: discord.Member,
        duracao: str,
        *,
        motivo: str
    ):
        erro = self._validar_alvo(ctx, membro, "aplicar timeout em")

        if erro:
            await ctx.send(erro, delete_after=8)
            return

        duracao_td = parse_duracao(duracao)

        await self._enviar_dm(
            membro,
            "⏳ Você recebeu timeout no Yoshizinho City",
            f"{motivo}\n\nDuração: {duracao}",
            ctx.author
        )

        await membro.timeout(
            duracao_td,
            reason=f"{motivo} | Responsável: {ctx.author} ({ctx.author.id})"
        )

        await self._registrar(
            ctx,
            membro,
            motivo,
            "timeout_manual",
            f"Timeout aplicado por {duracao}"
        )
        await ctx.send(f"✅ Timeout aplicado em {membro.mention} por `{duracao}`.")

    @commands.command(name="untimeout")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @eh_staff_com("moderate_members")
    async def untimeout(
        self,
        ctx,
        membro: discord.Member,
        *,
        motivo: str
    ):
        erro = self._validar_alvo(ctx, membro, "remover timeout de")

        if erro:
            await ctx.send(erro, delete_after=8)
            return

        await membro.timeout(
            None,
            reason=f"{motivo} | Responsável: {ctx.author} ({ctx.author.id})"
        )

        await self._registrar(
            ctx,
            membro,
            motivo,
            "untimeout_manual",
            "Timeout removido"
        )
        await ctx.send(f"✅ Timeout removido de {membro.mention}.")

    @commands.command(name="warn")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @eh_staff_com("manage_messages")
    async def warn(
        self,
        ctx,
        membro: discord.Member,
        *,
        motivo: str
    ):
        if membro.bot:
            await ctx.send("❌ Não registre warn manual em bots.", delete_after=8)
            return

        await self._registrar(
            ctx,
            membro,
            motivo,
            "warn_manual",
            "Aviso manual"
        )
        await ctx.send(f"✅ Warn registrado para {membro.mention}.")


async def setup(bot):
    await bot.add_cog(
        Moderacao(bot)
    )
