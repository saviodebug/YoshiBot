import discord
from discord.ext import commands

from utils.discord_db import registrar_booster


BOOSTER_ROLE_ID = 1085662246803353694


class Booster(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member
    ):
        cargo_booster = after.guild.get_role(
            BOOSTER_ROLE_ID
        )

        if cargo_booster is None:
            print(
                f"❌ Cargo Booster não encontrado: "
                f"{BOOSTER_ROLE_ID}"
            )
            return

        if (
            before.premium_since is None
            and after.premium_since is not None
        ):
            if cargo_booster not in after.roles:
                try:
                    await after.add_roles(
                        cargo_booster,
                        reason=(
                            "Usuário começou a dar boost "
                            "no servidor"
                        )
                    )

                    await registrar_booster(
                        self.bot,
                        after,
                        "iniciou",
                        cargo_booster
                    )

                    print(
                        f"💜 {after} começou a dar boost "
                        f"e recebeu {cargo_booster.name}"
                    )

                except discord.Forbidden:
                    print(
                        f"❌ Não consegui adicionar o cargo "
                        f"{cargo_booster.name} para {after}."
                    )

                except discord.HTTPException as erro:
                    print(
                        f"❌ Erro ao adicionar cargo Booster: {erro}"
                    )

                except Exception as erro:
                    print(
                        f"❌ Erro ao registrar Booster: {erro}"
                    )

        elif (
            before.premium_since is not None
            and after.premium_since is None
        ):
            if cargo_booster in after.roles:
                try:
                    await after.remove_roles(
                        cargo_booster,
                        reason=(
                            "Usuário deixou de dar boost "
                            "no servidor"
                        )
                    )

                    await registrar_booster(
                        self.bot,
                        after,
                        "encerrou",
                        cargo_booster
                    )

                    print(
                        f"💔 {after} deixou de dar boost "
                        f"e perdeu {cargo_booster.name}"
                    )

                except discord.Forbidden:
                    print(
                        f"❌ Não consegui remover o cargo "
                        f"{cargo_booster.name} de {after}."
                    )

                except discord.HTTPException as erro:
                    print(
                        f"❌ Erro ao remover cargo Booster: {erro}"
                    )

                except Exception as erro:
                    print(
                        f"❌ Erro ao registrar Booster: {erro}"
                    )


async def setup(bot):
    await bot.add_cog(
        Booster(bot)
    )
