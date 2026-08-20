import discord
from discord.ext import commands

from config import DISCORD_TOKEN


# =========================================================
# INTENTS
# =========================================================

intents = discord.Intents.all()


# =========================================================
# BOT
# =========================================================

class BotYoshi(commands.Bot):

    def __init__(self):

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )


    # =====================================================
    # CARREGAR COGS
    # =====================================================

    async def setup_hook(self):

        await self.load_extension(
            "cogs.informacoes"
        )

        await self.load_extension(
            "cogs.youtube"
        )

        await self.load_extension(
            "cogs.cargos"
        )

        await self.load_extension(
            "cogs.armadilha"
        )

        await self.load_extension(
            "cogs.midia"
        )

        await self.load_extension(
            "cogs.deletados"
        )

        await self.load_extension(
            "cogs.ticket"
        )

        await self.load_extension(
            "cogs.booster"
        )

        await self.load_extension(
            "cogs.erros"
        )

        await self.load_extension(
            "cogs.antispam"
        )

        await self.load_extension(
            "cogs.entradaEsaida"
        )

        await self.load_extension(
            "cogs.status"
        )

        await self.load_extension(
            "cogs.consultas"
        )

        await self.load_extension(
            "cogs.ajuda"
        )

        print(
            "✅ Módulos carregados!"
        )


    # =====================================================
    # BOT PRONTO
    # =====================================================

    async def on_ready(self):

        print(
            f"✅ O Bot {self.user} foi ligado com sucesso!"
        )

        print(
            f"📡 Ping: {round(self.latency * 1000)}ms"
        )

        print(
            f"🧩 Cogs carregados: {len(self.cogs)}"
        )


# =========================================================
# INICIAR BOT
# =========================================================

bot = BotYoshi()


bot.run(
    DISCORD_TOKEN
)
