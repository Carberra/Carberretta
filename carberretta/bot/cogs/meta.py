"""
META

Self:
    About;
    Bot info;
    Help;
    Source.
"""

from datetime import datetime, timedelta
from inspect import getsourcelines
from os.path import relpath
from platform import python_version
from subprocess import check_output
from sys import platform
from time import time
from typing import Optional

from discord import Embed
from discord import __version__ as discord_version
from discord.ext.commands import Cog, Command, command
from psutil import Process, virtual_memory

from carberretta import Config
from carberretta.utils import DEFAULT_EMBED_COLOUR, ROOT_DIR
from carberretta.utils.chron import short_delta
from carberretta.utils.converters import Command
from carberretta.utils.embed import build_embed


class Meta(Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bot.remove_command("help")

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @command(name="about")
    async def command_about(self, ctx):
        fields = (
            ("Authors", "\n".join(f"<@{id_}>" for id_ in Config.OWNER_IDS), False),
            ("Source", "Click [here](https://github.com/Carberra/Carberretta)", False),
            ("License", "[BSD 3-Clause](https://github.com/Carberra/Carberretta/blob/master/LICENSE)", False),
        )

        embed = build_embed(
            ctx=ctx,
            title="About Carberretta",
            description="Type `+info` for bot stats.",
            thumbnail=self.bot.user.avatar_url,
            fields=fields,
        )

        await ctx.send(embed=embed)

    @command(name="help")
    async def command_help(self, ctx, command: Optional[Command]):
        """This command. Invoke without any arguments for full help."""
        if command is None:
            pass
        else:
            syntax = "{} {}".format("|".join([str(command), *command.aliases]), command.signature)

            fields = (("Syntax", f"```+{syntax}```", False),)

            embed = build_embed(
                ctx=ctx,
                title=f"Help with `{command.name}`",
                description=command.help or "Not available.",
                colour=DEFAULT_EMBED_COLOUR,
                fields=fields,
            )

            await ctx.send(embed=embed)

    @command(name="botinfo", aliases=("bi", "info"))
    async def command_bot_info(self, ctx):
        proc = Process()
        with proc.oneshot():
            uptime = short_delta(timedelta(seconds=time() - proc.create_time()))
            cpu_time = short_delta(timedelta(seconds=(cpu := proc.cpu_times()).system + cpu.user))
            mem_total = virtual_memory().total / (1024 ** 2)
            mem_of_total = proc.memory_percent()
            mem_usage = mem_total * (mem_of_total / 100)

        if platform == "win32":
            loc = check_output(
                [
                    "powershell.exe",
                    f"(Get-ChildItem -Path \"{ROOT_DIR / 'carberretta'}\" | Get-ChildItem -Filter '*.py' -Recurse | Get-Content | Measure-Object -line).lines",
                ]
            )
        elif platform == "linux":
            loc = check_output(
                f"find {ROOT_DIR / 'carberretta'} -type f -name \"*.py\" -print0 | wc -l --files0-from=-"
            )
        else:
            loc = None

        fields = (
            ("Bot Version", self.bot.version, True),
            ("Python Version", python_version(), True),
            ("discord.py Version", discord_version, True),
            ("Uptime", uptime, True),
            ("CPU Time", cpu_time, True),
            ("Memory Usage", f"{mem_usage:,.3f} / {mem_total:,.0f} MiB ({mem_of_total:,.0f}%)", True),
            ("Users", self.bot.guild.member_count, True),
            ("Lines of Code", f"{int(loc):,}", True),
            ("Database Calls", f"{self.bot.db._calls:,}", True),
        )

        embed = build_embed(
            ctx=ctx,
            title="Carberretta Information",
            colour=DEFAULT_EMBED_COLOUR,
            thumbnail=self.bot.user.avatar_url,
            fields=fields,
        )

        await ctx.send(embed=embed)

    @command(name="source")
    async def command_source(self, ctx, command: Optional[Command]):
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


def setup(bot):
    bot.add_cog(Meta(bot))
