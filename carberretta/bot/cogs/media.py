"""
MEDIA

Controls media content such as Carberra video announcements.
Might extend to more.
"""

from discord.ext.commands import Cog


class Media(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)


def setup(bot):
    bot.add_cog(Media(bot))
