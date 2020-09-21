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
from carberretta.utils import DEFAULT_EMBED_COLOUR, ROOT_DIR
from carberretta.utils.chron import short_delta
from carberretta.utils.converters import Command


class Meta(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        # self.bot.remove_command("help")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @commands.command(name="about")
    async def command_about(self, ctx: commands.Context) -> None:
        await ctx.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "About Carberretta",
                    "description": "Type `+info` for bot stats.",
                    "color": DEFAULT_EMBED_COLOUR,
                    "thumbnail": {"url": f"{self.bot.user.avatar_url}"},
                    "author": {"name": "Carberretta"},
                    "footer": {
                        "text": f"Requested by {ctx.author.display_name}",
                        "icon_url": f"{ctx.author.avatar_url}",
                    },
                    "fields": [
                        {
                            "name": "Authors",
                            "value": "\n".join(f"<@{id_}>" for id_ in Config.OWNER_IDS),
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

    # @commands.command(name="help")
    # async def command_help(self, ctx: commands.Context, command: t.Optional[commands.Command]) -> None:
    #     """This command. Invoke without any arguments for full help."""
    #     print(command)
    #     if command is None:
    #         pass
    #     else:
    #         syntax = "{} {}".format("|".join([str(command), *command.aliases]), command.signature)

    #         await ctx.send(
    #             embed=discord.Embed.from_dict(
    #                 {
    #                     "title": f"Help with `{command.name}`",
    #                     "description": command.help or "Not available.",
    #                     "colour": DEFAULT_EMBED_COLOUR,
    #                     "thumbnail": {"url": f"{ctx.guild.icon_url}"},
    #                     "author": {"name": "Carberretta"},
    #                     "footer": {
    #                         "text": f"Requested by {ctx.author.display_name}",
    #                         "icon_url": f"{ctx.author.avatar_url}",
    #                     },
    #                     "fields": [{"name": "Syntax", "value": f"```+{syntax}```", "inline": False}],
    #                 }
    #             )
    #         )

    @commands.command(name="botinfo", aliases=("bi", "info"))
    async def command_bot_info(self, ctx: commands.Context) -> None:
        proc = Process()
        with proc.oneshot():
            uptime = short_delta(timedelta(seconds=time() - proc.create_time()))
            cpu_time = short_delta(timedelta(seconds=(cpu := proc.cpu_times()).system + cpu.user))
            mem_total = virtual_memory().total / (1024 ** 2)
            mem_of_total = proc.memory_percent()
            mem_usage = mem_total * (mem_of_total / 100)

        code, docs, empty = 0, 0, 0
        for subdir, _, files in os.walk(ROOT_DIR / "carberretta"):
            for file in (f for f in files if f.endswith(".py")):
                analysis = SourceAnalysis.from_file(f"{subdir}/{file}", "pygount", encoding="utf-8")
                code += analysis.code_count
                docs += analysis.documentation_count
                empty += analysis.empty_count

        await ctx.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "Carberretta Information",
                    "color": DEFAULT_EMBED_COLOUR,
                    "thumbnail": {"url": f"{self.bot.user.avatar_url}"},
                    "author": {"name": "Carberretta"},
                    "footer": {
                        "text": f"Requested by {ctx.author.display_name}",
                        "icon_url": f"{ctx.author.avatar_url}",
                    },
                    "fields": [
                        {"name": "Bot Version", "value": self.bot.version, "inline": True},
                        {"name": "Python Version", "value": python_version(), "inline": True},
                        {"name": "discord.py Version", "value": discord.__version__, "inline": True},
                        {"name": "Uptime", "value": uptime, "inline": True},
                        {"name": "CPU Time", "value": cpu_time, "inline": True},
                        {
                            "name": "Memory Usage",
                            "value": f"{mem_usage:,.3f} / {mem_total:,.0f} MiB ({mem_of_total:,.0f}%)",
                            "inline": True,
                        },
                        {"name": "Code Lines", "value": f"{int(code):,}", "inline": True},
                        {"name": "Docs Lines", "value": f"{int(docs):,}", "inline": True},
                        {"name": "Blank Lines", "value": f"{int(empty):,}", "inline": True},
                        {"name": "Database Calls", "value": f"{self.bot.db._calls:,}", "inline": True},
                    ],
                }
            )
        )

    @commands.command(name="source")
    async def command_source(self, ctx: commands.Context, command: t.Optional[commands.Command]) -> None:
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
        await self.bot.shutdown()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Meta(bot))
