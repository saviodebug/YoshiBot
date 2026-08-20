import discord
from discord.ext import commands


# =========================================================
# CARGOS E REAÇÕES
# =========================================================

CARGOS_REACOES = {
    "🔔": 1085662246732042329,  # Notificação
    "🔥": 1085662246757204148,  # fofozap
    "🎭": 1085662246757204147,  # Real Cria
    "😈": 1085662246757204146,  # METFLIX NO SOFA
    "💥": 1085662246757204145,  # RAJADX
    "🥷": 1085662246757204139,  # faixa Preta
    "❤️": 1085662246757204142,  # nao ame, faça amor
    "🔞": 1085662246757204143,  # +18
    "🧒": 1085662246757204144,  # -18
}


class Cargos(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # =====================================================
    # !CARGOS
    # =====================================================

    @commands.command(name="cargos")
    async def cargos(self, ctx):

        embed = discord.Embed(
            title="🎭 Escolha seus cargos",
            description=(
                "Personalize seu perfil escolhendo os cargos que combinam com você.\n\n"

                    "✨ **Como funciona?**\n"
    "Reaja com o emoji correspondente ao cargo que deseja receber.\n"
    "Para remover o cargo, basta retirar sua reação.\n\n"

    f"🔔 <@&1085662246732042329>\n"
    "Receba avisos de vídeos, lives e novidades.\n\n"

    f"🔥 <@&1085662246757204148>\n"
    "Reaja com 🔥\n\n"

    f"🎭 <@&1085662246757204147>\n"
    "Reaja com 🎭\n\n"

    f"😈 <@&1085662246757204146>\n"
    "Reaja com 😈\n\n"

    f"💥 <@&1085662246757204145>\n"
    "Reaja com 💥\n\n"

    f"🥷 <@&1085662246757204139>\n"
    "Reaja com 🥷\n\n"

    f"❤️ <@&1085662246757204142>\n"
    "Reaja com ❤️\n\n"

    "**🔞 Faixa etária**\n"
    f"🔞 → <@&1085662246757204143>\n"
    f"🧒 → <@&1085662246757204144>"
),
            color=discord.Color.from_rgb(
                0,
                170,
                255
            )
        )

        embed.set_footer(
            text="Yoshizinho City • Escolha seus cargos"
        )

        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

        mensagem = await ctx.send(
            embed=embed
        )

        # Adiciona automaticamente todas as reações
        for emoji in CARGOS_REACOES:
            await mensagem.add_reaction(emoji)


    # =====================================================
    # VERIFICAR SE É O PAINEL DE CARGOS
    # =====================================================

    async def verificar_painel(self, payload):

        canal = self.bot.get_channel(
            payload.channel_id
        )

        if canal is None:
            return None, None

        try:
            mensagem = await canal.fetch_message(
                payload.message_id
            )

        except (
            discord.NotFound,
            discord.Forbidden
        ):
            return None, None

        # Só aceita mensagens enviadas pelo próprio bot
        if mensagem.author.id != self.bot.user.id:
            return None, None

        # Verifica se existe embed
        if not mensagem.embeds:
            return None, None

        embed = mensagem.embeds[0]

        # Só aceita nosso painel
        if embed.title != "🎭 Escolha seus cargos":
            return None, None

        guild = self.bot.get_guild(
            payload.guild_id
        )

        return guild, mensagem


    # =====================================================
    # ADICIONAR CARGO
    # =====================================================

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        # Ignora reação do próprio bot
        if payload.user_id == self.bot.user.id:
            return

        emoji = str(payload.emoji)

        if emoji not in CARGOS_REACOES:
            return

        guild, mensagem = await self.verificar_painel(
            payload
        )

        if guild is None:
            return

        cargo_id = CARGOS_REACOES[emoji]

        cargo = guild.get_role(
            cargo_id
        )

        membro = guild.get_member(
            payload.user_id
        )

        if membro is None:
            try:
                membro = await guild.fetch_member(
                    payload.user_id
                )
            except discord.NotFound:
                return

        if cargo is None:
            print(
                f"❌ Cargo {cargo_id} não encontrado."
            )
            return


        # ---------------------------------------------
        # FAIXA ETÁRIA
        # Impede +18 e -18 ao mesmo tempo
        # ---------------------------------------------

        if cargo_id == 1085662246757204143:

            cargo_menor = guild.get_role(
                1085662246757204144
            )

            if (
                cargo_menor
                and cargo_menor in membro.roles
            ):
                await membro.remove_roles(
                    cargo_menor,
                    reason="Escolheu o cargo +18"
                )


        elif cargo_id == 1085662246757204144:

            cargo_maior = guild.get_role(
                1085662246757204143
            )

            if (
                cargo_maior
                and cargo_maior in membro.roles
            ):
                await membro.remove_roles(
                    cargo_maior,
                    reason="Escolheu o cargo -18"
                )


        try:

            await membro.add_roles(
                cargo,
                reason="Cargo por reação"
            )

            print(
                f"✅ {membro} recebeu {cargo.name}"
            )

        except discord.Forbidden:

            print(
                f"❌ Não tenho permissão para adicionar "
                f"o cargo {cargo.name}"
            )


    # =====================================================
    # REMOVER CARGO
    # =====================================================

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):

        emoji = str(payload.emoji)

        if emoji not in CARGOS_REACOES:
            return

        guild, mensagem = await self.verificar_painel(
            payload
        )

        if guild is None:
            return

        cargo_id = CARGOS_REACOES[emoji]

        cargo = guild.get_role(
            cargo_id
        )

        membro = guild.get_member(
            payload.user_id
        )

        if membro is None:
            try:
                membro = await guild.fetch_member(
                    payload.user_id
                )
            except discord.NotFound:
                return

        if cargo is None:
            return

        try:

            await membro.remove_roles(
                cargo,
                reason="Removeu reação do cargo"
            )

            print(
                f"➖ {membro} removeu {cargo.name}"
            )

        except discord.Forbidden:

            print(
                f"❌ Não tenho permissão para remover "
                f"o cargo {cargo.name}"
            )


async def setup(bot):

    await bot.add_cog(
        Cargos(bot)
    )