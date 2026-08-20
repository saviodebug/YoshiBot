from collections import deque

import discord
from discord.ext import commands

from config import LOG_DELETADOS_CHANNEL_ID


MAX_CONTENT_LENGTH = 2600
MAX_ATTACHMENTS_LENGTH = 900
RECENT_LOGGED_LIMIT = 250


def limitar_texto(
    texto: str,
    limite: int
) -> str:
    if len(texto) <= limite:
        return texto

    return f"{texto[:limite - 20]}\n...[texto cortado]"


def formatar_tamanho(
    tamanho: int | None
) -> str:
    if tamanho is None:
        return "tamanho desconhecido"

    unidades = (
        "B",
        "KB",
        "MB",
        "GB"
    )

    valor = float(tamanho)

    for unidade in unidades:
        if valor < 1024 or unidade == unidades[-1]:
            if unidade == "B":
                return f"{int(valor)} {unidade}"

            return f"{valor:.1f} {unidade}"

        valor /= 1024

    return f"{tamanho} B"


def formatar_anexos(
    anexos: list[discord.Attachment]
) -> str:
    linhas = []

    for anexo in anexos:
        detalhes = [
            formatar_tamanho(
                anexo.size
            )
        ]

        if anexo.content_type:
            detalhes.append(
                anexo.content_type
            )

        if anexo.url:
            detalhes.append(
                anexo.url
            )

        linhas.append(
            f"{anexo.filename} — "
            + " | ".join(
                detalhes
            )
        )

    if not linhas:
        return ""

    return limitar_texto(
        "\n".join(
            linhas
        ),
        MAX_ATTACHMENTS_LENGTH
    )


class GetDeletedUserIdButton(
    discord.ui.DynamicItem[discord.ui.Button],
    template=r"deleted:user:(?P<user_id>[0-9]+)"
):

    def __init__(
        self,
        user_id: int
    ):
        self.user_id = user_id

        super().__init__(
            discord.ui.Button(
                label="Get User ID",
                style=discord.ButtonStyle.secondary,
                custom_id=f"deleted:user:{user_id}"
            )
        )

    @classmethod
    async def from_custom_id(
        cls,
        interaction: discord.Interaction,
        item: discord.ui.Button,
        match
    ):
        return cls(
            int(
                match.group(
                    "user_id"
                )
            )
        )

    async def callback(
        self,
        interaction: discord.Interaction
    ):
        await interaction.response.send_message(
            f"ID do usuário: `{self.user_id}`",
            ephemeral=True
        )


class DeletedMessageView(discord.ui.View):

    def __init__(
        self,
        guild_id: int,
        channel_id: int,
        user_id: int | None = None
    ):
        super().__init__(
            timeout=None
        )

        if user_id is not None:
            self.add_item(
                GetDeletedUserIdButton(
                    user_id
                )
            )

        self.add_item(
            discord.ui.Button(
                label="Jump to Context",
                emoji="↗️",
                style=discord.ButtonStyle.link,
                url=(
                    "https://discord.com/channels/"
                    f"{guild_id}/{channel_id}"
                )
            )
        )


class EditedMessageView(discord.ui.View):

    def __init__(
        self,
        guild_id: int,
        channel_id: int,
        message_id: int
    ):
        super().__init__(
            timeout=None
        )

        self.add_item(
            discord.ui.Button(
                label="Jump to Message",
                emoji="↗️",
                style=discord.ButtonStyle.link,
                url=(
                    "https://discord.com/channels/"
                    f"{guild_id}/{channel_id}/{message_id}"
                )
            )
        )


class Deletados(commands.Cog):

    def __init__(
        self,
        bot
    ):
        self.bot = bot
        self._ids_logados = set()
        self._ordem_ids = deque(
            maxlen=RECENT_LOGGED_LIMIT
        )
        self._canal_nao_configurado_avisado = False

    async def cog_load(
        self
    ):
        self.bot.add_dynamic_items(
            GetDeletedUserIdButton
        )

    def _marcar_logado(
        self,
        message_id: int
    ):
        if len(self._ordem_ids) == self._ordem_ids.maxlen:
            antigo = self._ordem_ids.popleft()
            self._ids_logados.discard(
                antigo
            )

        self._ordem_ids.append(
            message_id
        )
        self._ids_logados.add(
            message_id
        )

    def _ja_logado(
        self,
        message_id: int
    ) -> bool:
        return message_id in self._ids_logados

    async def _obter_canal_log(
        self
    ) -> discord.TextChannel | None:
        if not LOG_DELETADOS_CHANNEL_ID:
            if not self._canal_nao_configurado_avisado:
                print(
                    "⚠️ LOG_DELETADOS_CHANNEL_ID ainda não foi configurado."
                )
                self._canal_nao_configurado_avisado = True

            return None

        canal = self.bot.get_channel(
            LOG_DELETADOS_CHANNEL_ID
        )

        if canal is None:
            try:
                canal = await self.bot.fetch_channel(
                    LOG_DELETADOS_CHANNEL_ID
                )

            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException
            ) as erro:
                print(
                    "❌ Não consegui acessar o canal de "
                    f"mensagens deletadas: {erro}"
                )
                return None

        if not isinstance(
            canal,
            discord.TextChannel
        ):
            print(
                "❌ LOG_DELETADOS_CHANNEL_ID não é um canal de texto."
            )
            return None

        return canal

    def _deve_ignorar_mensagem(
        self,
        message: discord.Message
    ) -> bool:
        if message.guild is None:
            return True

        if message.author.bot:
            return True

        if (
            self.bot.user
            and message.author.id == self.bot.user.id
        ):
            return True

        if message.channel.id == LOG_DELETADOS_CHANNEL_ID:
            return True

        return False

    async def _enviar_log_cacheado(
        self,
        message: discord.Message
    ):
        canal_log = await self._obter_canal_log()

        if canal_log is None:
            return

        conteudo = (
            message.clean_content
            or message.content
            or "[sem conteúdo de texto]"
        )

        conteudo = limitar_texto(
            conteudo,
            MAX_CONTENT_LENGTH
        )

        embed = discord.Embed(
            title="Message Deleted",
            description=(
                f"From: {message.author.mention}\n"
                f"In: {message.channel.mention}\n\n"
                "────────────────────\n\n"
                f"{conteudo}"
            ),
            color=discord.Color.from_rgb(
                220,
                120,
                45
            ),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="Original Message Time",
            value=discord.utils.format_dt(
                message.created_at,
                style="F"
            ),
            inline=False
        )

        anexos = formatar_anexos(
            list(
                message.attachments
            )
        )

        if anexos:
            embed.add_field(
                name="Arquivos anexados",
                value=anexos,
                inline=False
            )

        embed.set_footer(
            text=(
                f"Author: {message.author.id} | "
                f"Message ID: {message.id}"
            )
        )

        await canal_log.send(
            embed=embed,
            view=DeletedMessageView(
                message.guild.id,
                message.channel.id,
                message.author.id
            )
        )

    async def _enviar_log_minimo(
        self,
        payload: discord.RawMessageDeleteEvent
    ):
        canal_log = await self._obter_canal_log()

        if canal_log is None:
            return

        guild = self.bot.get_guild(
            payload.guild_id
        )

        canal = self.bot.get_channel(
            payload.channel_id
        )

        canal_texto = (
            canal.mention
            if isinstance(
                canal,
                discord.TextChannel
            )
            else f"`{payload.channel_id}`"
        )

        embed = discord.Embed(
            title="Message Deleted",
            description=(
                "Mensagem deletada sem dados em cache.\n\n"
                f"Canal: {canal_texto}\n"
                f"Message ID: `{payload.message_id}`"
            ),
            color=discord.Color.from_rgb(
                220,
                120,
                45
            ),
            timestamp=discord.utils.utcnow()
        )

        embed.set_footer(
            text=f"Message ID: {payload.message_id}"
        )

        await canal_log.send(
            embed=embed,
            view=DeletedMessageView(
                guild.id if guild else payload.guild_id,
                payload.channel_id
            )
        )

    async def _enviar_log_editado(
        self,
        before: discord.Message,
        after: discord.Message
    ):
        canal_log = await self._obter_canal_log()

        if canal_log is None:
            return

        antes = (
            before.clean_content
            or before.content
            or "[sem conteúdo de texto]"
        )

        depois = (
            after.clean_content
            or after.content
            or "[sem conteúdo de texto]"
        )

        embed = discord.Embed(
            title="✏️ Message Edited",
            description=(
                f"User: {after.author.mention}\n"
                f"Channel: {after.channel.mention}"
            ),
            color=discord.Color.from_rgb(
                240,
                170,
                55
            ),
            timestamp=discord.utils.utcnow()
        )

        embed.add_field(
            name="ANTES",
            value=limitar_texto(
                antes,
                900
            ),
            inline=False
        )

        embed.add_field(
            name="DEPOIS",
            value=limitar_texto(
                depois,
                900
            ),
            inline=False
        )

        embed.set_footer(
            text=(
                f"Author ID: {after.author.id} | "
                f"Message ID: {after.id}"
            )
        )

        await canal_log.send(
            embed=embed,
            view=EditedMessageView(
                after.guild.id,
                after.channel.id,
                after.id
            )
        )

    @commands.Cog.listener()
    async def on_message_delete(
        self,
        message: discord.Message
    ):
        if self._deve_ignorar_mensagem(
            message
        ):
            return

        if self._ja_logado(
            message.id
        ):
            return

        self._marcar_logado(
            message.id
        )

        await self._enviar_log_cacheado(
            message
        )

    @commands.Cog.listener()
    async def on_raw_message_delete(
        self,
        payload: discord.RawMessageDeleteEvent
    ):
        if payload.guild_id is None:
            return

        if payload.channel_id == LOG_DELETADOS_CHANNEL_ID:
            return

        if self._ja_logado(
            payload.message_id
        ):
            return

        if payload.cached_message is not None:
            return

        self._marcar_logado(
            payload.message_id
        )

        await self._enviar_log_minimo(
            payload
        )

    @commands.Cog.listener()
    async def on_message_edit(
        self,
        before: discord.Message,
        after: discord.Message
    ):
        if self._deve_ignorar_mensagem(
            before
        ):
            return

        if before.content == after.content:
            return

        await self._enviar_log_editado(
            before,
            after
        )


async def setup(
    bot
):
    await bot.add_cog(
        Deletados(
            bot
        )
    )
