import discord

from discord.ext import commands

from config import (
    WELCOME_CHANNEL_ID,
    RULES_CHANNEL_ID,
    CARGOS_CHANNEL_ID,
    AUTOMOD_CHANNEL_ID
)

from utils.logs import enviar_log


# =========================================================
# CONFIGURAÇÕES
# =========================================================

CARGO_MEMBRO_ID = 1085662246732042328


class Membros(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # =====================================================
    # ENTRADA
    # =====================================================

    @commands.Cog.listener()
    async def on_member_join(
        self,
        membro: discord.Member
    ):

        # =================================================
        # DAR CARGO DE MEMBRO AUTOMATICAMENTE
        # =================================================

        cargo_membro = membro.guild.get_role(
            CARGO_MEMBRO_ID
        )


        cargo_adicionado = False


        if cargo_membro is None:

            print(
                f"❌ Cargo Membros não encontrado: "
                f"{CARGO_MEMBRO_ID}"
            )


        else:

            try:

                await membro.add_roles(
                    cargo_membro,
                    reason=(
                        "Cargo automático ao entrar "
                        "no servidor"
                    )
                )


                cargo_adicionado = True


                print(
                    f"✅ {membro} recebeu automaticamente "
                    f"o cargo {cargo_membro.name}"
                )


            except discord.Forbidden:

                print(
                    f"❌ Não consegui adicionar o cargo "
                    f"{cargo_membro.name} para {membro}. "
                    f"Verifique a permissão Gerenciar Cargos "
                    f"e a hierarquia do bot."
                )


            except discord.HTTPException as erro:

                print(
                    f"❌ Erro ao adicionar cargo de membro "
                    f"para {membro}: {erro}"
                )


        # =================================================
        # CANAL DE BOAS-VINDAS
        # =================================================

        canal = self.bot.get_channel(
            WELCOME_CHANNEL_ID
        )


        if canal:

            embed = discord.Embed(

                title="💜 Bem-vindo(a) ao Yoshizinho City!",

                description=(
                    f"Olá {membro.mention}! 👋\n\n"

                    "É bom ter você por aqui.\n\n"

                    f"📜 Leia as regras em <#{RULES_CHANNEL_ID}>\n"
                    f"🎭 Escolha seus cargos em <#{CARGOS_CHANNEL_ID}>\n\n"

                    f"✅ Você recebeu automaticamente o cargo "
                    f"<@&{CARGO_MEMBRO_ID}>.\n\n"

                    "Divirta-se e aproveite a comunidade! 💜"
                ),

                color=discord.Color.from_rgb(
                    0,
                    170,
                    255
                )
            )


            embed.add_field(
                name="👥 Membros",
                value=str(
                    membro.guild.member_count
                ),
                inline=True
            )


            embed.add_field(
                name="🆔 ID",
                value=f"`{membro.id}`",
                inline=True
            )


            embed.set_thumbnail(
                url=membro.display_avatar.url
            )


            embed.set_footer(
                text="Yoshizinho City • Bem-vindo!"
            )


            try:

                await canal.send(
                    embed=embed
                )


            except discord.Forbidden:

                print(
                    "❌ Não tenho permissão para enviar "
                    "mensagem no canal de boas-vindas."
                )


            except discord.HTTPException as erro:

                print(
                    f"❌ Erro ao enviar boas-vindas: "
                    f"{erro}"
                )


        # =================================================
        # LOG DE ENTRADA
        # =================================================

        if cargo_membro:

            status_cargo = (
                cargo_membro.mention
                if cargo_adicionado
                else (
                    f"{cargo_membro.mention} "
                    f"⚠️ Não foi possível adicionar"
                )
            )

        else:

            status_cargo = (
                "❌ Cargo de membro não encontrado"
            )


        await enviar_log(
            self.bot,
            AUTOMOD_CHANNEL_ID,

            titulo="📥 Membro entrou",

            descricao=(
                "Um novo usuário entrou no servidor."
            ),

            cor=discord.Color.green(),

            campos=[
                {
                    "name": "👤 Usuário",
                    "value": (
                        f"{membro.mention}\n"
                        f"`{membro.id}`"
                    ),
                    "inline": True
                },

                {
                    "name": "🎭 Cargo automático",
                    "value": status_cargo,
                    "inline": True
                },

                {
                    "name": "👥 Total de membros",
                    "value": str(
                        membro.guild.member_count
                    ),
                    "inline": False
                }
            ]
        )


    # =====================================================
    # SAÍDA
    # =====================================================

    @commands.Cog.listener()
    async def on_member_remove(
        self,
        membro: discord.Member
    ):

        await enviar_log(
            self.bot,
            AUTOMOD_CHANNEL_ID,

            titulo="📤 Membro saiu",

            descricao=(
                "Um usuário deixou ou foi removido "
                "do servidor."
            ),

            cor=discord.Color.red(),

            campos=[
                {
                    "name": "👤 Usuário",
                    "value": (
                        f"**{membro}**\n"
                        f"`{membro.id}`"
                    ),
                    "inline": True
                },

                {
                    "name": "👥 Total de membros",
                    "value": str(
                        membro.guild.member_count
                    ),
                    "inline": True
                }
            ]
        )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):

    await bot.add_cog(
        Membros(bot)
    )