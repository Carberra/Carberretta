"""
PRESENCE

Handles presence updates.
"""

from collections import deque

from apscheduler.triggers.cron import CronTrigger
import discord
from discord.ext import commands

from carberretta import Config


class Presence(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self._name = "+help • {}"
        self._type = "watching"
        self._messages = deque(
            (
                "You can also mention the bot to invoke commands",
                "DM the bot to relay a message to the moderators",
                "Use the +source command to get the source code",
            )
        )

    @property
    def name(self) -> str:
        return self._name.format(self._messages[0])

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def type(self) -> discord.ActivityType:
        return getattr(discord.ActivityType, self._type, None)

    @type.setter
    def type(self, value: discord.ActivityType) -> None:
        self._type = value

    async def set(self) -> None:
        await self.bot.change_presence(activity=discord.Activity(name=self.name, type=self.type))
        self._messages.rotate(-1)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.bot.ready.up(self)


def setup(bot: commands.Bot) -> None:
    bot.add_cog((cog := Presence(bot)))
    bot.scheduler.add_job(cog.set, CronTrigger(second=0))
