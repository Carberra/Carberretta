"""
EXPERIENCE

Handles user experience stats:
    Experience attribution;
    Level rewarding;
    Opt-in and -out commands.
"""
import math

import discord
from discord.ext import commands

from carberretta import Config


class Experience(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def level_to_experience(self, level: int) -> int:
        return math.floor(sum(math.floor(x + 300 * 2 ** (x / 7.0)) for x in range(1, level)) / 4)

    async def experience_to_level(self, experience: int) -> int:
        level = 1
        while await self.level_to_experience(level) < experience:
            level += 1
        return level

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.bot.ready.up(self)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Experience(bot))
