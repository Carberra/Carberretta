"""
QT

Handles Jaxtar related things.
"""

import typing as t

import discord
from discord.ext import commands
from kaomoji.kaomoji import Kaomoji

from carberretta import Config
from carberretta.utils import checks, string


class Qt(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.kao = Kaomoji()
            self.qt_role = self.bot.guild.get_role(Config.QT_ROLE_ID)
            self.bot.ready.up(self)

    @commands.command(name="kaomoji", aliases=["kao"])
    async def kaomoji_command(self, ctx, category: t.Optional[str]):
        if category not in [*self.kao.categories, None]:
            return await ctx.send(f"Invalid category. Must be either {string.list_of(self.kao.categories, sep='or')}.")

        await ctx.send(self.kao.create(category))

    @commands.command(name="verifyqt")
    @checks.can_verify_qts()
    async def verifyqt_command(self, ctx: commands.Context, targets: commands.Greedy[discord.Member]):
        for target in targets:
            if self.qt_role not in target.roles:
                await target.add_roles(self.qt_role)
            await ctx.send(f"Done {self.kao.create('joy')}")

    @commands.command(name="unverifyqt")
    @checks.can_verify_qts()
    async def unverifyqt_command(self, ctx: commands.Context, targets: commands.Greedy[discord.Member]):
        for target in targets:
            if self.qt_role in target.roles:
                await target.remove_roles(self.qt_role)
            await ctx.send(f"Done {self.kao.create('sadness')}")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Qt(bot))
