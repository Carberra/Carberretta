"""
ROLE

Handles role based operations:
    Colour reactions;
    Opt-in and -out commands.
"""


import discord
from discord.ext import commands

from carberretta import Config


class Role(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.bot.ready.up(self)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Role(bot))
