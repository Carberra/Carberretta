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

import logging

import lightbulb

from carberretta.utils import string

log = logging.getLogger(__name__)

plugin = lightbulb.Plugin("Admin")


@plugin.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("shutdown", "Shut Carberretta down.", ephemeral=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_shutdown(ctx: lightbulb.SlashContext) -> None:
    log.info("Shutdown signal received")
    await ctx.respond("Now shutting down.")
    await ctx.bot.close()


@plugin.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option(
    "level", "The minimum logging level to view logs for.", choices="CEWIDT"
)
@lightbulb.command("logs", "View Carberretta's logs.", ephemeral=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_logs(ctx: lightbulb.SlashContext) -> None:
    if ctx.options.level == "T":
        # TRACE data runs across multiple lines. There's no point in
        # processing anyways, so just return the raw data.
        records = plugin.app.d.logs.getvalue()
    else:
        levels = "CEWID"
        idx = levels.index(ctx.options.level)
        records = "\n".join(
            filter(
                lambda x: any(f"[ {l} ]" in x for l in levels[: idx + 1]),
                plugin.app.d.logs.getvalue().strip().split("\n"),
            )
        )

    await ctx.respond(await string.binify(plugin.app.d.session, records, "logs"))


@plugin.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("id", "The error reference ID.")
@lightbulb.command("error", "View an error.")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_error(ctx: lightbulb.SlashContext) -> None:
    if len(search_id := ctx.options.id) < 5:
        await ctx.respond("Your search should be at least 5 characters long.")
        return

    row = await ctx.bot.d.db.try_fetch_record(
        "SELECT * FROM errors "
        "WHERE err_id LIKE ? || '%' "
        "ORDER BY err_time DESC "
        "LIMIT 1",
        search_id,
    )

    if not row:
        await ctx.respond("No errors matching that reference were found.")
        return

    await ctx.respond(
        await string.binify(
            plugin.app.d.session,
            f"Command: /{row.err_cmd}\nAt: {row.err_time}\n\n{row.err_text}",
            row.err_id,
        )
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
