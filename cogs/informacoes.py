import discord

from discord.ext import commands

from config import CARGO_MEMBROS_ID


class Informacoes(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # =====================================================
    # !REGRAS
    # =====================================================

    @commands.command(name="regras")
    async def regras(self, ctx):

        embed = discord.Embed(
            title="📜 Regras do Servidor",
            description=(
                "Leia atentamente as regras abaixo. Ao permanecer e interagir no "
                "**Yoshizinho City**, você concorda em respeitá-las.\n\n"

                "**1. 🤝 Respeito**\n"
                "Trate todos os membros com respeito. Ofensas, perseguição, racismo, "
                "homofobia, xenofobia ou qualquer tipo de preconceito não serão tolerados.\n\n"

                "**2. 🚫 Spam e Flood**\n"
                "Não envie mensagens repetidas, flood, marcações excessivas ou conteúdo "
                "com o objetivo de atrapalhar os canais.\n\n"

                "**3. 📢 Divulgação**\n"
                "Divulgações devem ser feitas somente nos canais permitidos. Não divulgue "
                "outros servidores, canais ou redes sociais fora dos espaços destinados a isso.\n\n"

                "**4. 🔞 Conteúdo impróprio**\n"
                "É proibido conteúdo NSFW, gore, golpes, phishing, arquivos maliciosos ou "
                "links suspeitos.\n\n"

                "**5. 💬 Organização**\n"
                "Utilize cada canal para a sua finalidade e evite assuntos fora do tema quando "
                "houver um espaço específico.\n\n"

                "**6. 🛡️ Staff**\n"
                "Respeite as orientações da equipe. Caso discorde de alguma decisão, abra "
                "um ticket e converse com a staff de forma privada.\n\n"

                "**7. 🔒 Privacidade**\n"
                "Não compartilhe informações pessoais, fotos ou dados de outros membros "
                "sem autorização.\n\n"

                "**8. ⚖️ Bom senso**\n"
                "Nem toda situação precisa estar descrita nas regras. A staff poderá agir diante "
                "de comportamentos que prejudiquem a comunidade.\n\n"

                f"<@&{CARGO_MEMBROS_ID}>"
            ),
            color=discord.Color.from_rgb(
                0,
                170,
                255
            )
        )

        embed.set_footer(
            text="Yoshizinho City • Respeite a comunidade e divirta-se."
        )

        try:
            await ctx.message.delete()

        except discord.Forbidden:
            pass

        await ctx.send(
            embed=embed
        )


    # =====================================================
    # !DIVULGACAO
    # =====================================================

    @commands.command(name="divulgacao")
    async def divulgacao(self, ctx):

        embed = discord.Embed(
            title="📢 Divulgação",
            description=(
                "Quer divulgar sua live, vídeo, canal ou outro conteúdo? Antes de publicar "
                "neste canal, é necessário solicitar a tag **Creator**.\n\n"

                "**🎟️ Como conseguir a tag Creator?**\n"
                "Abra um **ticket** e solicite a tag **Creator** para a staff. "
                "A equipe irá analisar o pedido e, caso aprovado, liberar o cargo.\n\n"

                "**🎥 Após ser aprovado**\n"
                "Com a tag **Creator**, você poderá utilizar este canal para divulgar suas lives, "
                "vídeos e conteúdos relacionados a games.\n\n"

                "**🚫 Não é permitido**\n"
                "• Divulgar sem a tag Creator\n"
                "• Fazer spam ou repostar o mesmo link repetidamente\n"
                "• Marcar @everyone ou @here\n"
                "• Divulgar conteúdo impróprio ou links suspeitos\n"
                "• Utilizar o canal para divulgação fora da proposta da comunidade\n\n"

                "**💡 Importante**\n"
                "A tag Creator não é automática. **Abra um ticket e aguarde a aprovação da "
                "staff antes de divulgar.**"
            ),
            color=discord.Color.from_rgb(
                0,
                170,
                255
            )
        )

        embed.set_footer(
            text="Yoshizinho City • Sistema de divulgação"
        )

        try:
            await ctx.message.delete()

        except discord.Forbidden:
            pass

        await ctx.send(
            embed=embed
        )


async def setup(bot):
    await bot.add_cog(
        Informacoes(bot)
    )