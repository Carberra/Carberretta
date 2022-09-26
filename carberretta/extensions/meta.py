# Copyright (c) 2020-present, Carberra
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import platform
import time
from dataclasses import dataclass

import hikari
import lightbulb
from psutil import Process, virtual_memory
from pygount import SourceAnalysis

import carberretta
from carberretta import Config
from carberretta.utils import chron, helpers

plugin = lightbulb.Plugin("Meta", include_datastore=True)
log = logging.getLogger(__name__)


@dataclass(slots=True)
class CodeCounter:
    code: int = 0
    docs: int = 0
    empty: int = 0
    files: int = 0

    def count(self) -> None:
        for i, file in enumerate(carberretta.ROOT_DIR.rglob("*.py"), start=1):
            analysis = SourceAnalysis.from_file(file, "pygount", encoding="utf-8")
            self.code += analysis.code_count
            self.docs += analysis.documentation_count
            self.empty += analysis.empty_count

        self.files = i
        plugin.d.loc = self
        log.info(f"counted loc in {self.files:,} files")


@plugin.listener(hikari.StartedEvent)
async def on_started(_: hikari.StartedEvent) -> None:
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, CodeCounter().count)


@plugin.command()
@lightbulb.command("ping", "Get the average DWSP latency for the bot.")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_ping(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond(
        f"Pong! DWSP latency: {ctx.bot.heartbeat_latency * 1_000:,.0f} ms."
    )


@plugin.command()
@lightbulb.command("about", "View information about Carberretta.")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_about(ctx: lightbulb.SlashContext) -> None:
    if not (guild := ctx.get_guild()):
        return

    if not (me := guild.get_my_member()):
        return

    if not (member := ctx.member):
        return

    with (proc := Process()).oneshot():
        uptime = time.time() - proc.create_time()
        uptime_str = chron.short_delta(dt.timedelta(seconds=uptime))
        cpu_time = chron.short_delta(
            dt.timedelta(seconds=(cpu := proc.cpu_times()).system + cpu.user),
            ms=True,
        )
        mem_total = virtual_memory().total / (1024**2)
        mem_of_total = proc.memory_percent()
        mem_usage = mem_total * (mem_of_total / 100)

    await ctx.respond(
        hikari.Embed(
            title="About Carberretta",
            description=(
                f"Authored by <@{Config.OWNER_ID}>. See all contributors on "
                f"[GitHub]({carberretta.__url__}/graphs/contributors). Licensed under "
                f"the [BSD 3-Clause]({carberretta.__url__}/blob/main/LICENSE) license."
            ),
            url="https://github.com/Carberra/Carberretta",
            colour=helpers.choose_colour(),
            timestamp=dt.datetime.now().astimezone(),
        )
        .set_thumbnail(me.avatar_url)
        .set_author(name="Bot Information")
        .set_footer(f"Requested by {member.display_name}", icon=member.avatar_url)
        .add_field("Bot version", carberretta.__version__, inline=True)
        .add_field("Python version", platform.python_version(), inline=True)
        .add_field("Hikari version", hikari.__version__, inline=True)
        .add_field("Uptime", uptime_str, inline=True)
        .add_field("CPU time", cpu_time, inline=True)
        .add_field(
            "Memory usage",
            f"{mem_usage:,.3f}/{mem_total:,.0f} MiB ({mem_of_total:,.0f}%)",
            inline=True,
        )
        .add_field("Code lines", f"{plugin.d.loc.code:,}", inline=True)
        .add_field("Docs lines", f"{plugin.d.loc.docs:,}", inline=True)
        .add_field("Blank lines", f"{plugin.d.loc.empty:,}", inline=True)
        .add_field(
            "Database calls",
            f"{(c := ctx.bot.d.db.calls):,} ({c/uptime:,.3f} per second)",
        )
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
