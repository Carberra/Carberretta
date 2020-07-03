"""
LOG

Handles event logging:
    Member updates;
    Message edits;
    Message deletions.
"""


from discord.ext.commands import Cog

from carberretta import Config


class Log(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)


def setup(bot):
    bot.add_cog(Log(bot))
