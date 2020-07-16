"""
PRESENCE

Handles presence updates.
"""

from collections import deque

from apscheduler.triggers.cron import CronTrigger
from discord import Activity, ActivityType
from discord.ext.commands import Cog

from carberretta import Config


class Presence(Cog):
    def __init__(self, bot):
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
    def name(self):
        return self._name.format(self._messages[0])

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def type(self):
        return getattr(ActivityType, self._type, None)

    @type.setter
    def type(self, value):
        self._type = value

    async def set(self):
        await self.bot.change_presence(activity=Activity(name=self.name, type=self.type))
        self._messages.rotate(-1)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)


def setup(bot):
    bot.add_cog((cog := Presence(bot)))
    bot.scheduler.add_job(cog.set, CronTrigger(second=0))
