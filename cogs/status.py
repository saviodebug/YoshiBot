import discord

from discord.ext import commands


class Status(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.iniciado_em = (
            discord.utils.utcnow()
        )


    @commands.command(
        name="status"
    )
    @commands.has_permissions(
        manage_guild=True
    )
    async def status(
        self,
        ctx
    ):

        # =================================================
        # PING
        # =================================================

        ping = round(
            self.bot.latency * 1000
        )


        # =================================================
        # YOUTUBE
        # =================================================

        youtube_cog = (
            self.bot.get_cog(
                "Youtube"
            )
        )


        youtube_status = "❌ Offline"


        if youtube_cog:

            loop = getattr(
                youtube_cog,
                "verificar_youtube",
                None
            )


            if (
                loop
                and loop.is_running()
            ):

                youtube_status = (
                    "✅ Funcionando"
                )


        # =================================================
        # COGS
        # =================================================

        quantidade_cogs = len(
            self.bot.cogs
        )


        # =================================================
        # TICKETS ABERTOS
        # =================================================

        tickets_abertos = 0


        for canal in ctx.guild.text_channels:

            if (
                canal.topic
                and "ticket_owner:" in canal.topic
            ):

                tickets_abertos += 1


        # =================================================
        # UPTIME
        # =================================================

        agora = discord.utils.utcnow()

        diferenca = (
            agora - self.iniciado_em
        )


        horas = int(
            diferenca.total_seconds()
            // 3600
        )


        minutos = int(
            (
                diferenca.total_seconds()
                % 3600
            )
            // 60
        )


        # =================================================
        # EMBED
        # =================================================

        embed = discord.Embed(

            title="🤖 Status do Yoshi's Bot",

            description=(
                "Informações atuais dos sistemas do bot."
            ),

            color=discord.Color.green(),

            timestamp=discord.utils.utcnow()
        )


        embed.add_field(
            name="🤖 Bot",
            value="✅ Online",
            inline=True
        )


        embed.add_field(
            name="📡 Ping",
            value=f"`{ping} ms`",
            inline=True
        )


        embed.add_field(
            name="▶️ YouTube",
            value=youtube_status,
            inline=True
        )


        embed.add_field(
            name="🧩 Módulos",
            value=(
                f"`{quantidade_cogs}` carregados"
            ),
            inline=True
        )


        embed.add_field(
            name="🎫 Tickets abertos",
            value=f"`{tickets_abertos}`",
            inline=True
        )


        embed.add_field(
            name="⏱️ Online há",
            value=(
                f"`{horas}h {minutos}min`"
            ),
            inline=True
        )


        embed.add_field(
            name="👥 Servidores",
            value=str(
                len(
                    self.bot.guilds
                )
            ),
            inline=True
        )


        embed.add_field(
            name="👤 Usuários",
            value=str(
                sum(
                    guild.member_count or 0
                    for guild in self.bot.guilds
                )
            ),
            inline=True
        )


        embed.set_thumbnail(
            url=self.bot.user.display_avatar.url
        )


        embed.set_footer(
            text="Yoshizinho City • Administração"
        )


        await ctx.send(
            embed=embed
        )


async def setup(bot):

    await bot.add_cog(
        Status(bot)
    )