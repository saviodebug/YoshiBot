import discord
import aiohttp

from discord.ext import commands, tasks

from config import (
    YOUTUBE_API_KEY,
    YOUTUBE_CHANNEL_ID,
    DISCORD_CHANNEL_ID,
    CARGO_NOTIFICACAO_ID
)


class Youtube(commands.Cog):

    def __init__(self, bot):

        self.bot = bot

        self.uploads_playlist_id = None
        self.videos_conhecidos = {}
        self.primeira_verificacao = True


    async def cog_load(self):

        self.verificar_youtube.start()

        print(
            "✅ Monitor do YouTube iniciado!"
        )


    def cog_unload(self):

        self.verificar_youtube.cancel()


    # =====================================================
    # PEGAR PLAYLIST DE UPLOADS
    # =====================================================

    async def pegar_playlist_uploads(self):

        url = (
            "https://www.googleapis.com/youtube/v3/channels"
            "?part=contentDetails"
            f"&id={YOUTUBE_CHANNEL_ID}"
            f"&key={YOUTUBE_API_KEY}"
        )

        async with aiohttp.ClientSession() as session:

            async with session.get(url) as response:

                dados = await response.json()

                print("Status YouTube:", response.status)


        if not dados.get("items"):

            print(
                "❌ Canal do YouTube não encontrado."
            )

            return None


        return (
            dados["items"][0]
            ["contentDetails"]
            ["relatedPlaylists"]
            ["uploads"]
        )


    # =====================================================
    # PEGAR ÚLTIMOS VÍDEOS
    # =====================================================

    async def pegar_ultimos_videos(self):

        if self.uploads_playlist_id is None:

            self.uploads_playlist_id = (
                await self.pegar_playlist_uploads()
            )


        if self.uploads_playlist_id is None:
            return []


        url_playlist = (
            "https://www.googleapis.com/youtube/v3/playlistItems"
            "?part=snippet"
            f"&playlistId={self.uploads_playlist_id}"
            "&maxResults=5"
            f"&key={YOUTUBE_API_KEY}"
        )


        async with aiohttp.ClientSession() as session:

            async with session.get(
                url_playlist
            ) as response:

                dados_playlist = (
                    await response.json()
                )


            video_ids = []


            for item in dados_playlist.get(
                "items",
                []
            ):

                video_id = (
                    item["snippet"]
                    ["resourceId"]
                    ["videoId"]
                )

                video_ids.append(
                    video_id
                )


            if not video_ids:
                return []


            ids = ",".join(
                video_ids
            )


            url_videos = (
                "https://www.googleapis.com/youtube/v3/videos"
                "?part=snippet,liveStreamingDetails"
                f"&id={ids}"
                f"&key={YOUTUBE_API_KEY}"
            )


            async with session.get(
                url_videos
            ) as response:

                dados_videos = (
                    await response.json()
                )


        return dados_videos.get(
            "items",
            []
        )


    # =====================================================
    # ENVIAR NOTIFICAÇÃO
    # =====================================================

    async def enviar_notificacao(
        self,
        video,
        tipo
    ):

        canal = self.bot.get_channel(
            DISCORD_CHANNEL_ID
        )


        if canal is None:

            print(
                "❌ Canal do Discord não encontrado."
            )

            return


        video_id = video["id"]

        snippet = video["snippet"]

        titulo = snippet["title"]


        thumbnails = snippet.get(
            "thumbnails",
            {}
        )


        if "maxres" in thumbnails:

            thumbnail = (
                thumbnails["maxres"]["url"]
            )


        elif "high" in thumbnails:

            thumbnail = (
                thumbnails["high"]["url"]
            )


        else:

            thumbnail = None


        link = (
            f"https://www.youtube.com/watch?v={video_id}"
        )


        # =================================================
        # LIVE
        # =================================================

        if tipo == "live":

            embed = discord.Embed(
                title="🔴 Yoshi está AO VIVO!",
                description=(
                    "O **Yoshi** acabou de entrar ao vivo "
                    "no YouTube! 💙\n\n"

                    f"🎮 **{titulo}**\n\n"

                    "👀 Cola lá, deixa o like e "
                    "fortalece a live!\n\n"

                    f"▶️ **[Assistir agora]({link})**"
                ),
                color=discord.Color.red()
            )


            mensagem = (
                f"<@&{CARGO_NOTIFICACAO_ID}> "
                "🔔 Tem **LIVE** no canal do Yoshi!"
            )


        # =================================================
        # VÍDEO
        # =================================================

        else:

            embed = discord.Embed(
                title="🚨 Conteúdo novo no canal!",
                description=(
                    "O **Yoshi** acabou de aparecer "
                    "no YouTube! 💙\n\n"

                    f"🎥 **{titulo}**\n\n"

                    "👀 Cola lá, deixa o like "
                    "e fortalece!\n\n"

                    f"▶️ **[Assistir agora]({link})**"
                ),
                color=discord.Color.from_rgb(
                    0,
                    170,
                    255
                )
            )


            mensagem = (
                f"<@1085662246732042329> "
                "🔔 Tem **vídeo novo** no canal do Yoshi!"
            )


        if thumbnail:

            embed.set_image(
                url=thumbnail
            )


        embed.set_footer(
            text="Yoshi • YouTube"
        )


        await canal.send(
            content=mensagem,
            embed=embed
        )


    # =====================================================
    # MONITOR DO YOUTUBE
    # =====================================================

    @tasks.loop(minutes=2)
    async def verificar_youtube(self):

        try:

            print(
                "🔎 Verificando YouTube..."
            )


            videos = (
                await self.pegar_ultimos_videos()
            )


            print(
                f"✅ {len(videos)} vídeos encontrados"
            )


            for video in videos:

                video_id = video["id"]

                titulo = (
                    video["snippet"]["title"]
                )


                status = (
                    video["snippet"].get(
                        "liveBroadcastContent",
                        "none"
                    )
                )


                print(
                    f"🎥 {titulo} | Status: {status}"
                )


                # PRIMEIRA VERIFICAÇÃO
                if self.primeira_verificacao:

                    self.videos_conhecidos[
                        video_id
                    ] = status

                    continue


                status_anterior = (
                    self.videos_conhecidos.get(
                        video_id
                    )
                )


                # =========================================
                # VÍDEO NOVO
                # =========================================

                if status_anterior is None:

                    self.videos_conhecidos[
                        video_id
                    ] = status


                    if status == "live":

                        await self.enviar_notificacao(
                            video,
                            "live"
                        )


                    elif status == "none":

                        await self.enviar_notificacao(
                            video,
                            "video"
                        )


                # =========================================
                # LIVE COMEÇOU
                # =========================================

                elif (
                    status_anterior != "live"
                    and status == "live"
                ):

                    self.videos_conhecidos[
                        video_id
                    ] = status


                    await self.enviar_notificacao(
                        video,
                        "live"
                    )


                else:

                    self.videos_conhecidos[
                        video_id
                    ] = status


            self.primeira_verificacao = False


        except Exception as erro:

            print(
                f"❌ Erro ao verificar YouTube: {erro}"
            )


    @verificar_youtube.before_loop
    async def antes_de_verificar_youtube(self):

        await self.bot.wait_until_ready()


    # =====================================================
    # !TESTVIDEO
    # =====================================================

    @commands.command(name="testvideo")
    async def testvideo(self, ctx):

        videos = (
            await self.pegar_ultimos_videos()
        )


        if not videos:

            await ctx.send(
                "❌ Nenhum vídeo encontrado."
            )

            return


        await self.enviar_notificacao(
            videos[0],
            "video"
        )


        try:
            await ctx.message.delete()

        except discord.Forbidden:
            pass


    # =====================================================
    # !TESTLIVE
    # =====================================================

    @commands.command(name="testlive")
    async def testlive(self, ctx):

        videos = (
            await self.pegar_ultimos_videos()
        )


        if not videos:

            await ctx.send(
                "❌ Nenhum vídeo encontrado."
            )

            return


        await self.enviar_notificacao(
            videos[0],
            "live"
        )


        try:
            await ctx.message.delete()

        except discord.Forbidden:
            pass


async def setup(bot):

    await bot.add_cog(
        Youtube(bot)
    )