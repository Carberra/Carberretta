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

import datetime as dt
import re

import hikari
import lightbulb

from carberretta.utils import chron

plugin = lightbulb.Plugin("Mod")

_chars = "".join(
    chr(i) for i in [*range(0x20, 0x30), *range(0x3A, 0x41), *range(0x5B, 0x61)]
)
UNHOIST_PATTERN = re.compile(rf"[{_chars}]+")
del _chars


@plugin.command()
@lightbulb.add_checks(
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES)
)
@lightbulb.option(
    "after", "A message ID to clear up to.", type=hikari.Message, required=False
)
@lightbulb.option(
    "member",
    "Only clear messages from this member.",
    type=hikari.Member,
    required=False,
)
@lightbulb.option("limit", "The number of messages to clear.", type=int)
@lightbulb.command(
    "clear",
    description="Clear messages in this channel.",
    ephemeral=True,
    auto_defer=True,
)
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_clear(ctx: lightbulb.SlashContext) -> None:
    if not (channel := ctx.get_channel()):
        return

    if not isinstance(channel, hikari.GuildTextChannel):
        return

    history = channel.fetch_history(
        after=ctx.options.after or chron.aware_now() - dt.timedelta(days=14)
    )
    if ctx.options.member:
        # Mypy is literally the worst piece of software ever written, I
        # swear to God. See python/mypy#9656 for more info.
        pred = lambda m: m.author.id == ctx.options.member.id
        history = history.filter(pred)
    messages = list(reversed(await history))

    for i in range(0, ctx.options.limit, 100):
        await channel.delete_messages(messages[i : min(i + 100, ctx.options.limit)])
    await ctx.respond(f"Cleared {min(ctx.options.limit, len(messages))} message(s).")


@plugin.command()
@lightbulb.add_checks(
    lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_NICKNAMES)
)
@lightbulb.command("unhoist", "Unhoist nicknames.", ephemeral=True, auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_unhoist(ctx: lightbulb.SlashContext) -> None:
    if not (guild := ctx.get_guild()):
        return

    count = 0

    for _, member in guild.get_members().items():
        if member.is_bot:
            continue

        match = UNHOIST_PATTERN.match(member.display_name)
        if not match:
            continue

        await member.edit(nickname=member.display_name.replace(match.group(), "", 1))
        count += 1

    await ctx.respond(f"Unhoisted {count:,} nicknames.")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
