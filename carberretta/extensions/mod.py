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
import logging

import hikari
import lightbulb

plugin = lightbulb.Plugin("Mod")

log = logging.getLogger(__name__)


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
        after=ctx.options.after
        or dt.datetime.now().astimezone() - dt.timedelta(days=14)
    )
    if ctx.options.member:
        history = history.filter(lambda m: m.author.id == ctx.options.member.id)
    messages = list(await history)

    for i in range(0, ctx.options.limit, 100):
        await channel.delete_messages(messages[i : i + 100])
    await ctx.respond(f"Cleared {min(ctx.options.limit, len(messages))} message(s).")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
