import discord
from discord.ext import commands
from config import AUTOMOD_CHANNEL_ID
from utils.logs import enviar_log

from config import ARMADILHA_CHANNEL_ID, AUTOMOD_CHANNEL_ID



class Armadilha(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # =====================================================
    # !ARMADILHA - PUBLICAR AVISO
    # =====================================================

    @commands.command(name="armadilha")
    @commands.has_permissions(manage_guild=True)
    async def armadilha(self, ctx):

        embed = discord.Embed(
            title="🛡️ Sistema de Segurança",
            description=(
                "Para proteger a comunidade contra **bots, spam e contas comprometidas**, "
                "alguns canais podem funcionar como **canais de armadilha**.\n\n"

                "**🚨 Como funciona?**\n"
                f"Enviar qualquer mensagem em <#{ARMADILHA_CHANNEL_ID}> pode acionar "
                "automaticamente o sistema de segurança do servidor.\n\n"

                "**⚠️ O que pode acontecer?**\n"
                "Ao enviar uma mensagem nesse canal, o usuário poderá ser "
                "**expulso automaticamente do servidor** e a mensagem será removida.\n\n"

                "**🤖 Por que usamos isso?**\n"
                "Bots, contas comprometidas e sistemas de spam costumam enviar mensagens "
                "automaticamente em diversos canais. A armadilha ajuda a identificar esse "
                "comportamento rapidamente.\n\n"

                "**💠 Foi um engano?**\n"
                "Caso tenha sido afetado por engano, entre em contato com a **staff** "
                "para que a situação seja analisada.\n\n"

                "**⛔ Não teste o canal por curiosidade.**\n"
                "Se você não faz parte da staff, simplesmente **não envie mensagens nele**."
            ),
            color=discord.Color.from_rgb(0, 170, 255)
        )

        embed.set_footer(
            text="Yoshizinho City • Segurança da comunidade"
        )

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        await ctx.send(embed=embed)


    # =====================================================
    # SISTEMA AUTOMÁTICO DA ARMADILHA
    # =====================================================

    @commands.Cog.listener()
    async def on_message(self, message):

        # Ignora mensagens fora de servidores
        if message.guild is None:
            return

        # Ignora bots
        if message.author.bot:
            return

        # Só funciona no canal da armadilha
        if message.channel.id != ARMADILHA_CHANNEL_ID:
            return

        membro = message.author


        # =================================================
        # PROTEÇÕES
        # =================================================

        # Não afeta administradores
        if membro.guild_permissions.administrator:
            return

        # Não afeta quem pode gerenciar o servidor
        if membro.guild_permissions.manage_guild:
            return


        print(
            f"🚨 Armadilha acionada por "
            f"{membro} ({membro.id})"
        )


        # =================================================
        # APAGAR A MENSAGEM
        # =================================================

        try:
            await message.delete()

        except discord.Forbidden:
            print(
                "❌ Sem permissão para apagar a mensagem."
            )


        # =================================================
        # AVISO NO PRIVADO
        # =================================================

        try:

            embed_dm = discord.Embed(
                title="🚨 Você foi removido do Yoshizinho City",
                description=(
                    "Nosso sistema de segurança detectou uma mensagem enviada em um "
                    "**canal de armadilha**.\n\n"

                    "Esse tipo de canal existe para identificar possíveis **bots, spam "
                    "ou contas comprometidas**.\n\n"

                    "O sistema identificou a ação como um possível comportamento automatizado "
                    "e, por segurança, sua conta foi **expulsa automaticamente do servidor**.\n\n"

                    "Se você acredita que isso aconteceu por engano, entre em contato "
                    "com a staff do **Yoshizinho City**."
                ),
                color=discord.Color.red()
            )

            embed_dm.set_footer(
                text="Yoshizinho City • Sistema de Segurança"
            )

            await membro.send(
                embed=embed_dm
            )

            print(
                f"📩 Aviso enviado no privado para {membro}"
            )

        except discord.Forbidden:

            print(
                f"⚠️ Não foi possível enviar DM para {membro}"
            )


        # =================================================
        # EXPULSAR O USUÁRIO
        # =================================================

        try:

            await membro.kick(
                reason=(
                    "Sistema de armadilha: "
                    "mensagem enviada no canal protegido."
                )
            )

            print(
                f"✅ {membro} foi expulso pela armadilha."
            )

            await enviar_log(
                self.bot,
                AUTOMOD_CHANNEL_ID,

                titulo="🚨 Armadilha acionada",

                cor=discord.Color.red(),

                campos=[
                    {
                        "name": "👤 Usuário",
                        "value": (
                            f"**{membro}**\n"
                            f"`{membro.id}`"
                        )
                    },

                    {
                        "name": "🔨 Ação",
                        "value": "Expulso do servidor"
                    },

                    {
                        "name": "🤖 Motivo",
                        "value": (
                            "Mensagem enviada no canal de armadilha."
                        )
                    }
                ]
            )


            # =============================================
            # AVISO PÚBLICO NO CANAL DA ARMADILHA
            # =============================================

            embed_log = discord.Embed(
                title="🚨 Usuário removido pela armadilha",
                description=(
                    "O sistema de segurança detectou uma atividade "
                    "no canal protegido e tomou uma ação automática."
                ),
                color=discord.Color.red()
            )

            embed_log.add_field(
                name="👤 Usuário",
                value=f"**{membro}**",
                inline=True
            )

            embed_log.add_field(
                name="🆔 ID",
                value=f"`{membro.id}`",
                inline=True
            )

            embed_log.add_field(
                name="⚠️ Ação",
                value="**Expulso do servidor**",
                inline=False
            )

            embed_log.add_field(
                name="🤖 Motivo",
                value=(
                    "Mensagem enviada no canal de armadilha. "
                    "Possível bot, spam ou conta comprometida."
                ),
                inline=False
            )

            embed_log.set_footer(
                text="Yoshizinho City • Sistema de Segurança"
            )

            canal_automod = self.bot.get_channel(
                AUTOMOD_CHANNEL_ID
            )

            if canal_automod is not None:
                await canal_automod.send(
                    embed=embed_log
                )
            else:
                print("❌ Canal de automod não encontrado.")


        except discord.Forbidden:

            print(
                f"❌ Não consegui expulsar {membro}. "
                "Confira as permissões e a hierarquia dos cargos."
            )


        except discord.HTTPException as erro:

            print(
                f"❌ Erro ao expulsar {membro}: {erro}"
            )


async def setup(bot):

    await bot.add_cog(
        Armadilha(bot)
    )