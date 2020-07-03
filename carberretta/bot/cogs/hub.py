"""
HUB

Handles hub operations.

**On cloned / forked versions, use root/.env to set alternative hub channels.**
"""


from discord.ext.commands import Cog

from carberretta import Config


class Hub(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.guild = self.bot.get_guild(Config.HUB_GUILD_ID)
            self.relay = self.bot.get_channel(Config.HUB_RELAY_ID)
            self.commands = self.bot.get_channel(Config.HUB_COMMANDS_ID)
            self.stdout = self.bot.get_channel(Config.HUB_STDOUT_ID)

            await self.stdout.send(f"Carberretta is now online! (Version {self.bot.version})")
            self.bot.ready.up(self)

    @Cog.listener()
    async def on_message(self, message):
        if not message.author.bot and (self.bot.user in message.mentions or "all" in message.content):
            if message.channel == self.commands:
                if message.content.startwith("shutdown"):
                    await self.bot.shutdown()

            elif message.channel == self.relay:
                pass


def setup(bot):
    bot.add_cog(Hub(bot))
