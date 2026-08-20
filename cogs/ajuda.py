import discord
from discord.ext import commands


# =========================================================
# CARGOS
# =========================================================

CARGOS_ADMIN = {

    1085662246828511249: "Direção",
    1085662246828511248: "Gerência",
    1085662246828511247: "Coordenação",
    1085662246828511246: "Supervisão",
    1085662246828511242: "Equipe Yoshi",

}

CARGO_MEMBRO_ID = 1085662246732042328


# =========================================================
# COG
# =========================================================

class Ajuda(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # =====================================================
    # IDENTIFICAR NÍVEL DO USUÁRIO
    # =====================================================

    def identificar_usuario(
        self,
        membro: discord.Member
    ):

        ids_cargos = {
            cargo.id
            for cargo in membro.roles
        }


        # =================================================
        # ADMIN
        # =================================================

        for cargo_id, cargo_nome in CARGOS_ADMIN.items():

            if cargo_id in ids_cargos:

                return (
                    "admin",
                    cargo_nome
                )


        # =================================================
        # MEMBRO
        # =================================================

        if CARGO_MEMBRO_ID in ids_cargos:

            return (
                "membro",
                "Membro"
            )


        # =================================================
        # NÃO IDENTIFICADO
        # =================================================

        return (
            "desconhecido",
            None
        )


    # =====================================================
    # !AJUDA
    # =====================================================

    @commands.command(
        name="ajuda",
        aliases=["help", "comandos"]
    )
    async def ajuda(
        self,
        ctx
    ):

        usuario = ctx.author


        if not isinstance(
            usuario,
            discord.Member
        ):

            return


        nivel, cargo_identificado = (
            self.identificar_usuario(
                usuario
            )
        )


        # =================================================
        # APAGAR !AJUDA
        # =================================================

        try:

            await ctx.message.delete()

        except discord.Forbidden:

            pass


        # =================================================
        # ADMIN
        # =================================================

        if nivel == "admin":

            embed = discord.Embed(

                title="🛠️ Central de Comandos • Administração",

                description=(
                    f"Olá {usuario.mention}! 👋\n\n"

                    "Você foi identificado como membro da "
                    "**Administração do Yoshizinho City**.\n\n"

                    f"**Cargo identificado:** `{cargo_identificado}`\n\n"

                    "Abaixo estão os comandos disponíveis para você."
                ),

                color=discord.Color.from_rgb(
                    0,
                    170,
                    255
                )
            )


            # =============================================
            # COMANDOS GERAIS
            # =============================================

            embed.add_field(

                name="👤 Comandos gerais",

                value=(
                    "`!ajuda`\n"
                    "Mostra esta central de comandos.\n\n"

                    "`!regras`\n"
                    "Publica o painel de regras.\n\n"

                    "`!divulgacao`\n"
                    "Publica o painel de divulgação e Creator.\n\n"

                    "`!cargos`\n"
                    "Publica o painel para escolha de cargos."
                ),

                inline=False
            )


            # =============================================
            # ADMINISTRAÇÃO
            # =============================================

            embed.add_field(

                name="🛡️ Administração",

                value=(
                    "`!ticket`\n"
                    "Publica a Central de Atendimento.\n\n"

                    "`!armadilha`\n"
                    "Publica/configura o sistema de armadilha.\n\n"

                    "`!status`\n"
                    "Mostra o status geral do bot.\n\n"

                    "`!ban @usuário motivo`\n"
                    "Bane um usuário e registra a ação.\n\n"

                    "`!kick @usuário motivo`\n"
                    "Expulsa um usuário e registra a ação.\n\n"

                    "`!timeout @usuário 10m motivo`\n"
                    "Aplica timeout temporário.\n\n"

                    "`!untimeout @usuário motivo`\n"
                    "Remove timeout de um usuário.\n\n"

                    "`!warn @usuário motivo`\n"
                    "Registra uma infração manual.\n\n"

                    "`!avaliacoes @staff`\n"
                    "Mostra avaliações recebidas por um atendente.\n\n"

                    "`!userinfo @usuário`\n"
                    "Mostra um resumo administrativo do usuário."
                ),

                inline=False
            )


            # =============================================
            # YOUTUBE
            # =============================================

            embed.add_field(

                name="▶️ YouTube • Testes",

                value=(
                    "`!testvideo`\n"
                    "Testa manualmente a notificação de vídeo.\n\n"

                    "`!testlive`\n"
                    "Testa manualmente a notificação de live."
                ),

                inline=False
            )


            # =============================================
            # SISTEMAS AUTOMÁTICOS
            # =============================================

            embed.add_field(

                name="🤖 Sistemas automáticos",

                value=(
                    "🛡️ Anti-Spam\n"
                    "🖼️ Controle de mídia\n"
                    "🚨 Canal-armadilha\n"
                    "💜 Cargo automático de Booster\n"
                    "▶️ Monitoramento do YouTube\n"
                    "🎫 Sistema de tickets\n"
                    "🙋 Assumir/liberar tickets\n"
                    "⭐ Avaliação de atendimento\n"
                    "🔊 Logs de voz\n"
                    "✏️ Logs de mensagens editadas\n"
                    "🗑️ Logs de mensagens deletadas\n"
                    "🎭 Logs de cargos e apelidos\n"
                    "📄 Transcript de tickets\n"
                    "📊 Logs de moderação\n"
                    "👋 Entrada e saída de membros"
                ),

                inline=False
            )


            embed.set_thumbnail(
                url=usuario.display_avatar.url
            )


            embed.set_footer(
                text=(
                    "Yoshizinho City • "
                    "Painel Administrativo"
                )
            )


            await ctx.send(
                embed=embed
            )

            return


        # =================================================
        # MEMBRO NORMAL
        # =================================================

        if nivel == "membro":

            embed = discord.Embed(

                title="📖 Central de Ajuda",

                description=(
                    f"Olá {usuario.mention}! 👋\n\n"

                    "Você foi identificado como "
                    "**membro do Yoshizinho City**.\n\n"

                    "Aqui estão os comandos disponíveis para você."
                ),

                color=discord.Color.from_rgb(
                    0,
                    170,
                    255
                )
            )


            embed.add_field(

                name="📚 Comandos",

                value=(
                    "`!ajuda`\n"
                    "Mostra esta central de ajuda.\n\n"

                    "`!regras`\n"
                    "Mostra as regras do servidor.\n\n"

                    "`!divulgacao`\n"
                    "Mostra informações sobre divulgação "
                    "e Creator.\n\n"

                    "`!cargos`\n"
                    "Mostra o painel para escolher seus cargos."
                ),

                inline=False
            )


            embed.add_field(

                name="🎫 Precisa de atendimento?",

                value=(
                    "Utilize o painel de **tickets** do servidor.\n\n"

                    "Você poderá escolher entre:\n"
                    "❓ Dúvida\n"
                    "🥳 Sorteio\n"
                    "🚫 Reportar alguém\n"
                    "▶️ Tag criador"
                ),

                inline=False
            )


            embed.set_thumbnail(
                url=usuario.display_avatar.url
            )


            embed.set_footer(
                text=(
                    "Yoshizinho City • "
                    "Central de Ajuda"
                )
            )


            await ctx.send(
                embed=embed
            )

            return


        # =================================================
        # SEM CARGO RECONHECIDO
        # =================================================

        embed = discord.Embed(

            title="⚠️ Cargo não identificado",

            description=(
                f"{usuario.mention}, não consegui identificar "
                "seu nível de acesso.\n\n"

                "Você ainda não possui o cargo de "
                "**Membro** ou algum cargo administrativo reconhecido.\n\n"

                "Caso isso esteja incorreto, entre em contato "
                "com a equipe do servidor."
            ),

            color=discord.Color.orange()
        )


        embed.set_thumbnail(
            url=usuario.display_avatar.url
        )


        embed.set_footer(
            text="Yoshizinho City • Central de Ajuda"
        )


        await ctx.send(
            embed=embed,
            delete_after=15
        )


# =========================================================
# SETUP
# =========================================================

async def setup(bot):

    await bot.add_cog(
        Ajuda(bot)
    )
