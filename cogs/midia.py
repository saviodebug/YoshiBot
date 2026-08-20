import discord
from discord.ext import commands
from config import AUTOMOD_CHANNEL_ID
from utils.logs import enviar_log

from config import CANAIS_MIDIA_PERMITIDOS


class Midia(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    # =====================================================
    # VERIFICAR SE O ARQUIVO É IMAGEM OU VÍDEO
    # =====================================================

    def eh_midia(self, attachment):

        # Primeiro tenta verificar pelo content-type
        if attachment.content_type:

            if attachment.content_type.startswith("image/"):
                return True

            if attachment.content_type.startswith("video/"):
                return True


        # Caso o Discord não informe o content-type,
        # verifica pela extensão
        extensoes_midia = (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".webp",
            ".bmp",
            ".heic",
            ".mp4",
            ".mov",
            ".avi",
            ".mkv",
            ".webm",
            ".m4v"
        )

        nome_arquivo = attachment.filename.lower()

        return nome_arquivo.endswith(extensoes_midia)


    # =====================================================
    # SISTEMA DE BLOQUEIO
    # =====================================================

    @commands.Cog.listener()
    async def on_message(self, message):

        # Ignora DMs
        if message.guild is None:
            return

        # Ignora bots
        if message.author.bot:
            return


        membro = message.author


        # =================================================
        # MODERADORES PODEM
        # =================================================

        if membro.guild_permissions.administrator:
            return

        if membro.guild_permissions.manage_messages:
            return


        # =================================================
        # VERIFICA O CANAL
        # =================================================

        canal_id = message.channel.id

        # Caso seja uma thread, verifica também
        # o canal pai
        canal_pai_id = getattr(
            message.channel,
            "parent_id",
            None
        )


        if (
            canal_id in CANAIS_MIDIA_PERMITIDOS
            or canal_pai_id in CANAIS_MIDIA_PERMITIDOS
        ):
            return


        # =================================================
        # VERIFICA SE TEM IMAGEM OU VÍDEO
        # =================================================

        tem_midia = any(
            self.eh_midia(attachment)
            for attachment in message.attachments
        )


        if not tem_midia:
            return


        # =================================================
        # APAGA A MENSAGEM
        # =================================================

        try:

            await message.delete()

            print(
                f"🗑️ Mídia removida de {membro} "
                f"no canal #{message.channel}"
            )


        except discord.Forbidden:

            print(
                "❌ Não tenho permissão para apagar "
                "a mensagem."
            )

            return

        await enviar_log(
            self.bot,
            AUTOMOD_CHANNEL_ID,

            titulo="🖼️ Mídia removida",

            cor=discord.Color.orange(),

            campos=[
                {
                    "name": "👤 Usuário",
                    "value": (
                        f"{membro.mention}\n"
                        f"`{membro.id}`"
                    )
                },

                {
                    "name": "📍 Canal",
                    "value": message.channel.mention
                },

                {
                    "name": "⚠️ Motivo",
                    "value": (
                        "Imagem ou vídeo enviado "
                        "em canal não autorizado."
                    )
                }
            ]
        )


        # =================================================
        # AVISA O USUÁRIO
        # =================================================

        try:

            aviso = await message.channel.send(
                f"{membro.mention}, imagens e vídeos não são "
                "permitidos neste canal.\n"
                "Use <#1085662261433094224> para enviar "
                "imagens, memes e vídeos."
            )

            # Apaga o aviso depois de 8 segundos
            await aviso.delete(
                delay=8
            )

        except discord.Forbidden:
            pass


async def setup(bot):

    await bot.add_cog(
        Midia(bot)
    )