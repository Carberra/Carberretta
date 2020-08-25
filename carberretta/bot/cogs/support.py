"""
SUPPORT

Handles support channels.
Provides tag and message archiving funcionalities.
"""

import typing
from collections import defaultdict
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from carberretta import Config


INACTIVE_TIME: typing.Final = 15 * 60


class Support(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def move_to_available(self, channel: discord.TextChannel) -> None:
        if await channel.history(
            limit=1, after=datetime.utcnow() - timedelta(seconds=max(0, INACTIVE_TIME - 1))
        ).flatten():
            self.bot.scheduler.add_job(
                self.move_to_available,
                "date",
                run_date=datetime.now() + timedelta(seconds=INACTIVE_TIME),
                args=[channel],
            )
        else:
            await channel.edit(category=self.available_category, reason="Support case became inactive.")

    @commands.command(name="close", aliases=["done"])
    async def command_close(self, ctx):
        await ctx.channel.edit(category=self.available_category, reason="Support case was closed.")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.available_category = self.bot.get_channel(735284663916167332)  # Temp
            self.in_use_category = self.bot.get_channel(735284697411616788)  # Temp
            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if self.bot.ready.ok:
            if isinstance(message.channel, discord.TextChannel):
                if message.channel.category == self.available_category:
                    await message.channel.edit(category=self.in_use_category, reason="Support case initiated.")
                    self.bot.scheduler.add_job(
                        self.move_to_available,
                        "date",
                        run_date=datetime.now() + timedelta(seconds=INACTIVE_TIME),
                        args=[message.channel],
                    )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Support(bot))
