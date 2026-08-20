import discord
from discord.ext import commands

from config import LOG_MEMBROS_CHANNEL_ID


class AuditoriaMembros(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self._aviso_config = False

    async def _canal_log(self):
        if not LOG_MEMBROS_CHANNEL_ID:
            if not self._aviso_config:
                print("⚠️ LOG_MEMBROS_CHANNEL_ID ainda não foi configurado.")
                self._aviso_config = True

            return None

        canal = self.bot.get_channel(LOG_MEMBROS_CHANNEL_ID)

        if canal is None:
            try:
                canal = await self.bot.fetch_channel(LOG_MEMBROS_CHANNEL_ID)
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as erro:
                print(f"❌ Não consegui acessar o canal de logs de membros: {erro}")
                return None

        if not isinstance(canal, discord.TextChannel):
            print("❌ LOG_MEMBROS_CHANNEL_ID não é um canal de texto.")
            return None

        return canal

    async def _buscar_executor(
        self,
        guild: discord.Guild,
        target_id: int,
        action: discord.AuditLogAction
    ) -> discord.User | discord.Member | None:
        if guild.me is None or not guild.me.guild_permissions.view_audit_log:
            return None

        agora = discord.utils.utcnow()

        try:
            async for entrada in guild.audit_logs(limit=5, action=action):
                alvo = getattr(entrada, "target", None)

                if getattr(alvo, "id", None) != target_id:
                    continue

                if (agora - entrada.created_at).total_seconds() > 15:
                    continue

                return entrada.user

        except (discord.Forbidden, discord.HTTPException):
            return None

        return None

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
            print("❌ Sem permissão para enviar logs de membros.")

    def _executor_texto(self, executor):
        if executor is None:
            return "Não identificado"

        return f"{executor.mention}\n`{executor.id}`"

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member
    ):
        if after.bot:
            return

        if before.nick != after.nick:
            executor = await self._buscar_executor(
                after.guild,
                after.id,
                discord.AuditLogAction.member_update
            )

            await self._enviar(
                "✏️ Apelido alterado",
                discord.Color.blurple(),
                [
                    {"name": "Usuário", "value": f"{after.mention}\n`{after.id}`", "inline": False},
                    {"name": "Antes", "value": before.nick or before.name, "inline": True},
                    {"name": "Depois", "value": after.nick or after.name, "inline": True},
                    {"name": "Executado por", "value": self._executor_texto(executor), "inline": False},
                ],
                f"user_id={after.id};event=nickname"
            )

        cargos_antes = {
            cargo.id: cargo
            for cargo in before.roles
            if not cargo.is_default()
        }

        cargos_depois = {
            cargo.id: cargo
            for cargo in after.roles
            if not cargo.is_default()
        }

        adicionados = [
            cargos_depois[cargo_id]
            for cargo_id in cargos_depois.keys() - cargos_antes.keys()
        ]

        removidos = [
            cargos_antes[cargo_id]
            for cargo_id in cargos_antes.keys() - cargos_depois.keys()
        ]

        if not adicionados and not removidos:
            return

        executor = await self._buscar_executor(
            after.guild,
            after.id,
            discord.AuditLogAction.member_role_update
        )

        for cargo in adicionados:
            await self._enviar(
                "✅ Cargo adicionado",
                discord.Color.green(),
                [
                    {"name": "Usuário", "value": f"{after.mention}\n`{after.id}`", "inline": True},
                    {"name": "Cargo", "value": f"{cargo.mention}\n`{cargo.id}`", "inline": True},
                    {"name": "Executado por", "value": self._executor_texto(executor), "inline": False},
                ],
                f"user_id={after.id};role_id={cargo.id};event=role_added"
            )

        for cargo in removidos:
            await self._enviar(
                "➖ Cargo removido",
                discord.Color.red(),
                [
                    {"name": "Usuário", "value": f"{after.mention}\n`{after.id}`", "inline": True},
                    {"name": "Cargo", "value": f"{cargo.name}\n`{cargo.id}`", "inline": True},
                    {"name": "Executado por", "value": self._executor_texto(executor), "inline": False},
                ],
                f"user_id={after.id};role_id={cargo.id};event=role_removed"
            )


async def setup(bot):
    await bot.add_cog(
        AuditoriaMembros(bot)
    )
