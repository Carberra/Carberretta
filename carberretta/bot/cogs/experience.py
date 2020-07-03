"""
EXPERIENCE

Handles user experience stats:
    Experience attribution;
    Level rewarding;
    Opt-in and -out commands.
"""


from discord.ext.commands import Cog

from carberretta import Config


class Experience(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)


def setup(bot):
    bot.add_cog(Experience(bot))
