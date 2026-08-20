import discord
from discord.ext import commands

from config import LOG_SISTEMA_CHANNEL_ID
from utils.logs import enviar_log


class Erros(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx,
        error
    ):
        if isinstance(
            error,
            commands.CommandNotFound
        ):
            return

        if isinstance(
            error,
            commands.CheckFailure
        ):
            await ctx.send(
                "❌ Você não possui permissão para usar este comando.",
                delete_after=6
            )
            return

        if isinstance(
            error,
            commands.MissingPermissions
        ):
            await ctx.send(
                "❌ Você não possui permissão para usar este comando.",
                delete_after=6
            )
            return

        if isinstance(
            error,
            commands.BotMissingPermissions
        ):
            await ctx.send(
                "❌ Eu não tenho as permissões necessárias "
                "para executar esse comando.",
                delete_after=6
            )
            return

        if isinstance(
            error,
            commands.MissingRequiredArgument
        ):
            await ctx.send(
                "⚠️ Faltou alguma informação no comando.",
                delete_after=6
            )
            return

        if isinstance(
            error,
            commands.BadArgument
        ):
            await ctx.send(
                "⚠️ Não consegui entender um dos argumentos do comando.",
                delete_after=6
            )
            return

        erro_real = getattr(
            error,
            "original",
            error
        )

        print(
            f"❌ Erro no comando {ctx.command}: {erro_real}"
        )

        await enviar_log(
            self.bot,
            LOG_SISTEMA_CHANNEL_ID,
            titulo="⚠️ Erro no bot",
            descricao=(
                "Um erro não tratado ocorreu durante "
                "a execução de um comando."
            ),
            cor=discord.Color.red(),
            campos=[
                {
                    "name": "⌨️ Comando",
                    "value": f"`{ctx.message.content[:500]}`"
                },
                {
                    "name": "👤 Usuário",
                    "value": (
                        f"{ctx.author.mention}\n"
                        f"`{ctx.author.id}`"
                    )
                },
                {
                    "name": "❌ Erro",
                    "value": (
                        f"```{str(erro_real)[:900]}```"
                    )
                }
            ]
        )


async def setup(bot):
    await bot.add_cog(
        Erros(bot)
    )
