"""
META

Self:
    About;
    Bot info;
    Help;
    Source.
"""

import os
import typing as t
from datetime import datetime, timedelta
from inspect import getsourcelines
from os.path import relpath
from platform import python_version
from subprocess import check_output
from sys import platform
from time import time

import discord
from discord.ext import commands
from psutil import Process, virtual_memory
from pygount import SourceAnalysis

from carberretta import Config
from carberretta.utils import DEFAULT_EMBED_COLOUR, ROOT_DIR, chron, converters, string


class Meta(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.contributors = [self.bot.guild.get_member(id_) for id_ in (*Config.OWNER_IDS, 219255057022058498)]
            self.bot.ready.up(self)

    @commands.command(name="about")
    async def command_about(self, ctx: commands.Context) -> None:
        await ctx.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "About Carberretta",
                    "description": "Use `+botinfo` for detailed statistics.",
                    "color": DEFAULT_EMBED_COLOUR,
                    "thumbnail": {"url": f"{self.bot.user.avatar_url}"},
                    "author": {"name": "Information"},
                    "footer": {
                        "text": f"Requested by {ctx.author.display_name}",
                        "icon_url": f"{ctx.author.avatar_url}",
                    },
                    "fields": [
                        {
                            "name": "Contributors",
                            "value": string.list_of([m.mention for m in self.contributors]),
                            "inline": False,
                        },
                        {
                            "name": "Source",
                            "value": "Click [here](https://github.com/Carberra/Carberretta)",
                            "inline": False,
                        },
                        {
                            "name": "License",
                            "value": "[BSD 3-Clause](https://github.com/Carberra/Carberretta/blob/master/LICENSE)",
                            "inline": False,
                        },
                    ],
                }
            )
        )

    @commands.command(name="botinfo", aliases=("bi", "info"))
    async def command_bot_info(self, ctx: commands.Context) -> None:
        proc = Process()
        with proc.oneshot():
            uptime = chron.short_delta(timedelta(seconds=time() - proc.create_time()))
            cpu_time = chron.short_delta(
                timedelta(seconds=(cpu := proc.cpu_times()).system + cpu.user), milliseconds=True
            )
            mem_total = virtual_memory().total / (1024 ** 2)
            mem_of_total = proc.memory_percent()
            mem_usage = mem_total * (mem_of_total / 100)

        await ctx.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "Bot information",
                    "description": "Use `+about` for licensing and development information.",
                    "color": DEFAULT_EMBED_COLOUR,
                    "thumbnail": {"url": f"{self.bot.user.avatar_url}"},
                    "author": {"name": "Information"},
                    "footer": {
                        "text": f"Requested by {ctx.author.display_name}",
                        "icon_url": f"{ctx.author.avatar_url}",
                    },
                    "fields": [
                        {"name": "Bot version", "value": self.bot.version, "inline": True},
                        {"name": "Python version", "value": python_version(), "inline": True},
                        {"name": "discord.py version", "value": discord.__version__, "inline": True},
                        {"name": "Uptime", "value": uptime, "inline": True},
                        {"name": "CPU time", "value": cpu_time, "inline": True},
                        {
                            "name": "Memory usage",
                            "value": f"{mem_usage:,.3f} / {mem_total:,.0f} MiB ({mem_of_total:,.0f}%)",
                            "inline": True,
                        },
                        {"name": "Code lines", "value": f"{int(self.bot.loc.code):,}", "inline": True},
                        {"name": "Docs lines", "value": f"{int(self.bot.loc.docs):,}", "inline": True},
                        {"name": "Blank lines", "value": f"{int(self.bot.loc.empty):,}", "inline": True},
                        {"name": "Database calls", "value": f"{self.bot.db._calls:,}", "inline": True},
                    ],
                }
            )
        )

    @commands.command(name="source")
    async def command_source(self, ctx: commands.Context, command: t.Optional[converters.Command]) -> None:
        source_url = "https://github.com/Carberra/Carberretta"

        if command is None:
            await ctx.send(f"<{source_url}>")
        else:
            src = command.callback.__code__
            module = command.callback.__module__
            filename = src.co_filename
            lines, firstlineno = getsourcelines(src)

            if not module.startswith("discord"):
                location = relpath(filename).replace("\\", "/")
            else:
                source_url = "https://github.com/Rapptz/discord.py"
                location = module.replace(".", "/") + ".py"

            await ctx.send(f"<{source_url}/blob/master/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>")

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown_command(self, ctx: commands.Context) -> None:
        # Prefer hub shutdown where possible.
        await ctx.message.delete()
        await self.bot.close()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Meta(bot))
