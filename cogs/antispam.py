import re
import time
from collections import defaultdict, deque
from datetime import timedelta
from urllib.parse import urlparse

import discord
from discord.ext import commands

from config import ARMADILHA_CHANNEL_ID
from utils.discord_db import (
    contar_infracoes_24h,
    registrar_infracao,
)


class AntiSpam(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        self.mensagens = defaultdict(
            lambda: deque(maxlen=30)
        )

        self.ultimo_trigger = {}

        self.regex_convite = re.compile(
            r"(discord\.gg/|discord(?:app)?\.com/invite/)",
            re.IGNORECASE
        )

        self.dominios_suspeitos = {
            "grabify.link",
            "iplogger.org",
            "iplogger.com",
            "2no.co",
            "yip.su"
        }

    def eh_moderador(
        self,
        membro: discord.Member
    ) -> bool:
        return (
            membro.guild_permissions.administrator
            or membro.guild_permissions.manage_messages
            or membro.guild_permissions.manage_guild
        )

    def possui_link_suspeito(
        self,
        texto: str
    ) -> bool:
        urls = re.findall(
            r"https?://[^\s]+",
            texto
        )

        for url in urls:
            try:
                dominio = urlparse(url).hostname

                if not dominio:
                    continue

                dominio = dominio.lower()

                if dominio.startswith("xn--"):
                    return True

                if dominio in self.dominios_suspeitos:
                    return True

            except Exception:
                continue

        return False

    async def punir(
        self,
        message: discord.Message,
        motivo: str,
        tipo: str
    ):
        membro = message.author
        agora = time.monotonic()

        ultimo = self.ultimo_trigger.get(
            membro.id,
            0
        )

        if agora - ultimo < 10:
            try:
                await message.delete()
            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ):
                pass

            return

        self.ultimo_trigger[
            membro.id
        ] = agora

        try:
            infracoes_anteriores = await contar_infracoes_24h(
                self.bot,
                membro.id
            )

        except Exception as erro:
            print(
                f"❌ Não consegui consultar infrações: {erro}"
            )
            infracoes_anteriores = 0

        nivel = infracoes_anteriores + 1
        conteudo_original = message.content

        try:
            await message.delete()

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException
        ):
            pass

        if nivel == 1:
            acao = "Aviso"

            try:
                await message.channel.send(
                    f"⚠️ {membro.mention}, essa mensagem "
                    f"foi identificada pelo Anti-Spam.\n"
                    f"**Motivo:** {motivo}",
                    delete_after=8
                )

            except discord.Forbidden:
                pass

        elif nivel == 2:
            acao = "Timeout de 10 minutos"

            try:
                await membro.timeout(
                    timedelta(minutes=10),
                    reason=f"Anti-Spam: {motivo}"
                )

            except discord.Forbidden:
                acao += " (falhou: sem permissão)"

        elif nivel == 3:
            acao = "Timeout de 1 hora"

            try:
                await membro.timeout(
                    timedelta(hours=1),
                    reason=f"Anti-Spam: {motivo}"
                )

            except discord.Forbidden:
                acao += " (falhou: sem permissão)"

        else:
            acao = "Expulso do servidor"

            try:
                await membro.kick(
                    reason=f"Anti-Spam: {motivo}"
                )

            except discord.Forbidden:
                acao += " (falhou: sem permissão)"

        try:
            await registrar_infracao(
                self.bot,
                membro,
                motivo,
                tipo,
                acao,
                message.channel,
                conteudo_original
            )

        except Exception as erro:
            print(
                f"❌ Não consegui registrar a infração: {erro}"
            )

    @commands.Cog.listener()
    async def on_message(
        self,
        message: discord.Message
    ):
        if message.guild is None:
            return

        if message.author.bot:
            return

        membro = message.author

        if self.eh_moderador(
            membro
        ):
            return

        if message.channel.id == ARMADILHA_CHANNEL_ID:
            return

        agora = time.monotonic()

        texto = (
            message.content
            .strip()
            .lower()
        )

        historico = self.mensagens[
            membro.id
        ]

        historico.append(
            (
                agora,
                texto
            )
        )

        mensagens_5s = [
            item
            for item in historico
            if agora - item[0] <= 5
        ]

        if len(mensagens_5s) >= 6:
            await self.punir(
                message,
                "Flood: muitas mensagens em poucos segundos",
                "flood"
            )
            return

        if texto:
            repetidas = [
                item
                for item in historico
                if (
                    agora - item[0] <= 20
                    and item[1] == texto
                )
            ]

            if len(repetidas) >= 3:
                await self.punir(
                    message,
                    "Mensagem repetida várias vezes",
                    "repeticao"
                )
                return

        numero_mencoes = (
            len(message.mentions)
            +
            len(message.role_mentions)
        )

        if numero_mencoes >= 5:
            await self.punir(
                message,
                "Excesso de menções",
                "mencoes"
            )
            return

        if self.regex_convite.search(
            message.content
        ):
            await self.punir(
                message,
                "Convite de servidor Discord não autorizado",
                "convite"
            )
            return

        if self.possui_link_suspeito(
            message.content
        ):
            await self.punir(
                message,
                "Link potencialmente suspeito",
                "link_suspeito"
            )
            return


async def setup(bot):
    await bot.add_cog(
        AntiSpam(bot)
    )
