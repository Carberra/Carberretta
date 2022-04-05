# Copyright (c) 2020-2021, Carberra Tutorials
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

import datetime as dt
import platform
import time
from dataclasses import dataclass

import hikari
import lightbulb
from psutil import Process, virtual_memory
from pygount import SourceAnalysis

import carberretta
from carberretta import Config
from carberretta.utils import chron, helpers, rtfm

import requests

plugin = lightbulb.Plugin("Meta", include_datastore=True)


@dataclass
class CodeCounter:
    code: int = 0
    docs: int = 0
    empty: int = 0

    def count(self) -> CodeCounter:
        for file in carberretta.ROOT_DIR.rglob("*.py"):
            analysis = SourceAnalysis.from_file(file, "pygount", encoding="utf-8")
            self.code += analysis.code_count
            self.docs += analysis.documentation_count
            self.empty += analysis.empty_count

        return self


@plugin.command
@lightbulb.command("ping", "Get the average DWSP latency for the bot.")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_ping(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond(
        f"Pong! DWSP latency: {ctx.bot.heartbeat_latency * 1_000:,.0f} ms."
    )


@plugin.command
@lightbulb.command("about", "View information about Carberretta.")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_about(ctx: lightbulb.SlashContext) -> None:
    if not (guild := ctx.get_guild()):
        return

    if not (me := guild.get_my_member()):
        return

    if not (member := ctx.member):
        return

    await ctx.respond(
        hikari.Embed(
            title="About Carberretta",
            description="Type `/stats` for bot runtime stats.",
            colour=helpers.choose_colour(),
            timestamp=dt.datetime.now().astimezone(),
        )
        .set_thumbnail(me.avatar_url)
        .set_author(name="Information")
        .set_footer(f"Requested by {member.display_name}", icon=member.avatar_url)
        .add_field("Authors", "\n".join(f"<@{i}>" for i in Config.OWNER_IDS))
        .add_field(
            "Contributors",
            f"View on [GitHub]({carberretta.__url__}/graphs/contributors)",
        )
        .add_field(
            "License",
            '[BSD 3-Clause "New" or "Revised" License]'
            f"({carberretta.__url__}/blob/main/LICENSE)",
        )
    )


@plugin.command
@lightbulb.command("stats", "View runtime stats for Carberretta.")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_stats(ctx: lightbulb.SlashContext) -> None:
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
        mem_total = virtual_memory().total / (1024 ** 2)
        mem_of_total = proc.memory_percent()
        mem_usage = mem_total * (mem_of_total / 100)

    await ctx.respond(
        hikari.Embed(
            title="Runtime statistics for Carberretta",
            description="Type `/about` for general bot information.",
            colour=helpers.choose_colour(),
            timestamp=dt.datetime.now().astimezone(),
        )
        .set_thumbnail(me.avatar_url)
        .set_author(name="Information")
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
        .add_field("Code lines", f"{ctx.bot.d.loc.code:,}", inline=True)
        .add_field("Docs lines", f"{ctx.bot.d.loc.docs:,}", inline=True)
        .add_field("Blank lines", f"{ctx.bot.d.loc.empty:,}", inline=True)
        .add_field(
            "Database calls",
            f"{(c := ctx.bot.d.db.calls):,} ({c/uptime:,.3f} per second)",
        )
    )

@plugin.command
@lightbulb.command("rtfm", description="Searches the docs of hikari and lightbulb.")
@lightbulb.implements(lightbulb.SlashCommandGroup, lightbulb.PrefixCommandGroup)
async def rtfm_group(ctx) -> None:
    pass

@rtfm.child
@lightbulb.option("query", "The query to search for", autocomplete=True, required=True)
@lightbulb.command("hikari", description="Searches the docs of hikari.", auto_defer=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def hikari_rtfm(ctx) -> None:
    matches = await rtfm.get_autocomplete(ctx.options.query, "hikari")
    embed = hikari.Embed(title="RTFM", color=color.default)
    embed.description = ""
    for match in matches:
        try:
            embed.description += f"[`{match}`](https://www.hikari-py.dev/{plugin.d.hikari_cache[match][1]})\n"
        except:
            continue
    await ctx.respond(embed=embed)

@rtfm.child
@lightbulb.option("query", "The query to search for", autocomplete=True, required=True)
@lightbulb.command("lightbulb", description="Searches the docs of lightbulb.", auto_defer=True)
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def lightbulb_rtfm(ctx) -> None:
    matches = await rtfm.get_autocomplete(ctx.options.query, "lightbulb")
    embed = hikari.Embed(title="RTFM", color=0x2f3136) #I just put no color, idk what you want
    embed.description = ""
    for match in matches:
        try:
            embed.description += f"[`{match}`](https://hikari-lightbulb.readthedocs.io/en/latest/{plugin.d.lightbulb_cache[match][1]})\n" #I didn't know you can make these things clickible. Cool.
        except:
            continue
    await ctx.respond(embed=embed)

@hikari_rtfm.autocomplete("query")
async def hikari_autocomplete(opt: hikari.AutocompleteInteractionOption, inter: hikari.AutocompleteInteraction): return await rtfm.get_rtfm(opt.value, plugin.d.hikari_cache)

@lightbulb_rtfm.autocomplete("query")
async def lightbulb_autocomplete(opt: hikari.AutocompleteInteractionOption, inter: hikari.AutocompleteInteraction): return await rtfm.get_rtfm(opt.value, plugin.d.lightbulb_cache)

def load(bot: lightbulb.BotApp) -> None:
    if not bot.d.loc:
        bot.d.loc = CodeCounter().count()
    bot.add_plugin(plugin)
    # This just gets the docs stuff
    response = requests.get("https://www.hikari-py.dev/" + "objects.inv")
    cache = rtfm.decode_object_inv(response.content) #decodes it
    plugin.d.hikari_cache = cache
    response = requests.get("https://hikari-lightbulb.readthedocs.io/en/latest/" + "objects.inv")
    cache = rtfm.decode_object_inv(response.content) #decodes it
    plugin.d.lightbulb_cache = cache


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
