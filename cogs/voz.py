import discord
from discord.ext import commands

from config import LOG_VOZ_CHANNEL_ID


class Voz(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._entradas = {}
        self._aviso_config = False

    async def _canal_log(self):
        if not LOG_VOZ_CHANNEL_ID:
            if not self._aviso_config:
                print("⚠️ LOG_VOZ_CHANNEL_ID ainda não foi configurado.")
                self._aviso_config = True

            return None

        canal = self.bot.get_channel(LOG_VOZ_CHANNEL_ID)

        if canal is None:
            try:
                canal = await self.bot.fetch_channel(LOG_VOZ_CHANNEL_ID)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as erro:
                print(f"❌ Não consegui acessar o canal de logs de voz: {erro}")
                return None

        if not isinstance(canal, discord.TextChannel):
            print("❌ LOG_VOZ_CHANNEL_ID não é um canal de texto.")
            return None

        return canal

    async def _enviar(
        self,
        titulo: str,
        cor: discord.Color,
        campos: list[dict],
        footer: str
    ):
        canal = await self._canal_log()

        if canal is None:
            return

        embed = discord.Embed(
            title=titulo,
            color=cor,
            timestamp=discord.utils.utcnow()
        )

        for campo in campos:
            embed.add_field(
                name=campo["name"],
                value=campo["value"],
                inline=campo.get("inline", False)
            )

        embed.set_footer(text=footer)

        try:
            await canal.send(embed=embed)
        except discord.Forbidden:
            print("❌ Sem permissão para enviar logs de voz.")

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        if member.bot:
            return

        agora = discord.utils.utcnow()

        if before.channel is None and after.channel is not None:
            self._entradas[member.id] = agora

            await self._enviar(
                "🔊 Entrou no canal de voz",
                discord.Color.green(),
                [
                    {"name": "Usuário", "value": f"{member.mention}\n`{member.id}`", "inline": True},
                    {"name": "Canal", "value": f"{after.channel.mention}\n`{after.channel.id}`", "inline": True},
                ],
                f"user_id={member.id};to_channel_id={after.channel.id}"
            )
            return

        if before.channel is not None and after.channel is None:
            entrada = self._entradas.pop(member.id, None)
            tempo = "Não calculado"

            if entrada is not None:
                minutos = max(0, round((agora - entrada).total_seconds() / 60))
                tempo = f"{minutos} minuto(s)"

            await self._enviar(
                "🔇 Saiu do canal de voz",
                discord.Color.red(),
                [
                    {"name": "Usuário", "value": f"{member.mention}\n`{member.id}`", "inline": True},
                    {"name": "Canal", "value": f"{before.channel.mention}\n`{before.channel.id}`", "inline": True},
                    {"name": "Tempo aproximado conectado", "value": tempo, "inline": False},
                ],
                f"user_id={member.id};from_channel_id={before.channel.id}"
            )
            return

        if (
            before.channel is not None
            and after.channel is not None
            and before.channel.id != after.channel.id
        ):
            await self._enviar(
                "🔁 Mudou de canal de voz",
                discord.Color.blurple(),
                [
                    {"name": "Usuário", "value": f"{member.mention}\n`{member.id}`", "inline": False},
                    {"name": "De", "value": f"{before.channel.mention}\n`{before.channel.id}`", "inline": True},
                    {"name": "Para", "value": f"{after.channel.mention}\n`{after.channel.id}`", "inline": True},
                ],
                (
                    f"user_id={member.id};"
                    f"from_channel_id={before.channel.id};"
                    f"to_channel_id={after.channel.id}"
                )
            )

        if before.mute != after.mute:
            await self._enviar(
                "🎙️ Mute de servidor alterado",
                discord.Color.orange(),
                [
                    {"name": "Usuário", "value": f"{member.mention}\n`{member.id}`", "inline": True},
                    {"name": "Status", "value": "Mutado" if after.mute else "Desmutado", "inline": True},
                ],
                f"user_id={member.id};voice_mute={int(after.mute)}"
            )

        if before.deaf != after.deaf:
            await self._enviar(
                "🔇 Deaf de servidor alterado",
                discord.Color.orange(),
                [
                    {"name": "Usuário", "value": f"{member.mention}\n`{member.id}`", "inline": True},
                    {"name": "Status", "value": "Ensurdecido" if after.deaf else "Desensurdecido", "inline": True},
                ],
                f"user_id={member.id};voice_deaf={int(after.deaf)}"
            )


async def setup(bot):
    await bot.add_cog(
        Voz(bot)
    )
