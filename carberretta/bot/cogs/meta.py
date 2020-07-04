"""
META

Self:
    About;
    Bot info;
    Help;
    Source.
"""

from datetime import datetime, timedelta
from platform import python_version
from subprocess import check_output
from sys import argv, platform
from time import time
from typing import Optional

from discord import Embed, __version__ as discord_version
from discord.ext.commands import Cog, Command, command
from psutil import Process, virtual_memory

from carberretta import Config
from carberretta.utils import ROOT_DIR
from carberretta.utils.chron import short_delta


class Meta(Cog):
    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @command(name="about")
    async def about(self, ctx):
        embed = Embed(title="About Carberretta",
                      description="Type `+info` for bot stats.",
                      colour=ctx.author.colour,
                      timestamp=datetime.utcnow())
        embed.set_thumbnail(url=self.bot.user.avatar_url)

        fields = (
            ("Authors", "\n".join(f"<@{id_}>" for id_ in Config.OWNER_IDS), False),
            ("Source", "Click [here](https://github.com/Carberra/Carberretta)", False),
            ("License", "[BSD 3-Clause](https://github.com/Carberra/Carberretta/blob/master/LICENSE)", False),
        )

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        await ctx.send(embed=embed)

    @command(name="help2")
    async def command_help(self, ctx, command: Optional[Command]):
        if cmd:
            embed = Embed(title=f"Help for {cmd.name}",
                          description=cmd.help,
                          colour=self.bot.guild.me.colour,
                          timestamp=datetime.utcnow())

            syntax = "{} {}".format("|".join([str(command), *command.aliases]), command.signature)

            fields = (
                ("Syntax", f"```+{syntax}```", False),
            )

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            await ctx.send(embed=embed)

        else:
            pass

    @command(name="info")
    async def command_info(self, ctx):
        embed = Embed(title="Carberretta Information",
                      colour=self.bot.guild.me.colour,
                      timestamp=datetime.utcnow())
        embed.set_thumbnail(url=self.bot.user.avatar_url)

        proc = Process()
        with proc.oneshot():
            uptime = short_delta(timedelta(seconds=time()-proc.create_time()))
            cpu_time = short_delta(timedelta(seconds=(cpu := proc.cpu_times()).system+cpu.user))
            mem_total = virtual_memory().total/(1024**2)
            mem_of_total = proc.memory_percent()
            mem_usage = mem_total*(mem_of_total/100)

        if platform == "win32":
            loc = check_output(f"(Get-ChildItem -Path \"{ROOT_DIR / 'carberretta'}\" | Get-ChildItem -Filter '*.py' -Recurse | Get-Content | Measure-Object -line).lines")
        elif platform == "linux":
            loc = check_output(f"find {ROOT_DIR / 'carberretta'} -type f -name \"*.py\" -print0 | wc -l --files0-from=-")
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

        for name, value, inline in fields:
            embed.add_field(name=name, value=value, inline=inline)

        await ctx.send(embed=embed)

    @command(name="source")
    async def command_source(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Meta(bot))
