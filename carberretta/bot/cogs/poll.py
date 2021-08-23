"""
POLL

Handles polls.
"""

import random
import typing as t
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from carberretta import Config
from carberretta.utils import chron


class Poll(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self._cache: t.List[discord.Message] = []

    @commands.group(name="poll", aliases=["p"])
    @commands.has_permissions(administrator=True)
    async def poll(self, ctx) -> None:
        pass

    @poll.command(name="help")
    @commands.has_permissions(administrator=True)
    async def help_command(self, ctx):
        await ctx.send("+poll create <stack> <time> <question> [options]...")

    @poll.command(name="create")
    @commands.has_permissions(administrator=True)
    async def command_create(self, ctx, stack: bool, time: int, question: str, *options) -> None:
        if len(options) > 20:
            raise commands.TooManyArguments

        await ctx.message.delete()

        message = discord.utils.get(
            self.bot.cached_messages,
            id=(
                await ctx.send(
                    embed=discord.Embed.from_dict(
                        {
                            "title": "Poll",
                            "description": question,
                            "color": random.randint(0, 0xFFFFFF),
                            "footer": {"text": "React to cast a vote!"},
                            "fields": [
                                {
                                    "name": "Options",
                                    "value": "\n".join(
                                        [f"{chr(0x1f1e6 + i)} {option}" for i, option in enumerate(options)]
                                    ),
                                    "inline": False,
                                },
                                {
                                    "name": "End time",
                                    "value": f"{chron.long_date_and_time(datetime.utcnow() + timedelta(seconds=time))} UTC",
                                    "inline": False,
                                },
                            ],
                        }
                    )
                )
            ).id,
        )

        for i in range(len(options)):
            await message.add_reaction(chr(0x1F1E6 + i))

        if not stack:
            self._cache.append(message)

        self.bot.scheduler.add_job(
            self.resolve, "date", run_date=datetime.utcnow() + timedelta(seconds=time), args=[message]
        )

    async def resolve(self, message: discord.Message) -> None:
        # TODO: Improve this mess
        max_value = 0
        most_voted = []
        for r in message.reactions:
            value = 0
            async for user in r.users():
                if patron_role := discord.utils.find(lambda r: r.name.startswith("Tier"), user.roles):
                    value += (int(patron_role.name[5]) + 1) // 2

                value += 1

            if value > max_value:
                most_voted = [r.emoji]
                max_value = value
            elif value == max_value:
                most_voted.append(r.emoji)
        self._cache.remove(message)

        await message.channel.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "Poll Result",
                    "description": f"{message.embeds[0].description}\n\n"
                    + f"Click [here]({message.jump_url}) to see the original message.",
                    "color": message.embeds[0].colour.value,
                    "footer": {"text": "Thanks to everyone who voted!"},
                    "fields": [
                        {
                            "name": f"Winner{'s' if len(most_voted) > 1 else ''}",
                            "value": ", ".join(most_voted),
                            "inline": True,
                        },
                        {"name": "Count", "value": max_value - 1, "inline": True},
                    ],
                }
            )
        )

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        if not payload.member.bot:
            if message := discord.utils.get(self._cache, id=payload.message_id):
                for emoji in (
                    reaction.emoji for reaction in message.reactions if reaction.emoji != payload.emoji.name
                ):
                    await message.remove_reaction(emoji, payload.member)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Poll(bot))
