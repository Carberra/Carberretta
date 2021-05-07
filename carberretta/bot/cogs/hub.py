"""
HUB

Handles hub operations.

**On cloned / forked versions, use root/.env to set alternative hub channels.**
"""

import discord
from discord.ext import commands

from carberretta import Config


class Hub(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.guild = self.bot.get_guild(Config.HUB_GUILD_ID)
            self.relay = self.bot.get_channel(Config.HUB_RELAY_ID)
            self.commands = self.bot.get_channel(Config.HUB_COMMANDS_ID)
            self.stdout = self.bot.get_channel(Config.HUB_STDOUT_ID)

            await self.stdout.send(f"Carberretta is now online! (Version {self.bot.version})")
            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.author.bot and (self.bot.user in message.mentions or "all" in message.content):
            if message.channel == self.commands:
                if message.content.startswith("shutdown"):
                    await self.bot.close()

            elif message.channel == self.relay:
                pass


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Hub(bot))
