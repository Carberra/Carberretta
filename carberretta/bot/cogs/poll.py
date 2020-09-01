"""
POLL

Handles polls.
"""

import typing as t
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from carberretta import Config


class Poll(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self._cache: t.List[discord.Message] = []

    @commands.group(name="poll", aliases=["p"])
    async def poll(self, ctx) -> None:
        pass

    @poll.command(name="create")
    async def command_create(self, ctx, stack: bool, time: int, question: str, *options) -> None:
        if len(options) > 20:
            raise commands.TooManyArguments

        message = discord.utils.get(
            self.bot.cached_messages,
            id=(
                await ctx.send(
                    embed=discord.Embed.from_dict(
                        {
                            "title": "Poll",
                            "fields": [
                                {"name": "Question", "value": question, "inline": False},
                                {"name": "Instructions", "value": "React to cast a vote!", "inline": False},
                                {
                                    "name": "Options",
                                    "value": "\n".join(
                                        [f"{chr(0x1f1e6 + i)} {option}" for i, option in enumerate(options)]
                                    ),
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
            self.resolve, "date", run_date=datetime.now() + timedelta(seconds=time), args=[message]
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

        await message.channel.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "Poll Result",
                    "fields": [
                        message.embeds[0].fields[0].__dict__,
                        {"name": "Original Poll", "value": f"[Jump]({message.jump_url})", "inline": False},
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
                    try:
                        await message.remove_reaction(emoji, payload.member)
                    except:
                        raise


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Poll(bot))
