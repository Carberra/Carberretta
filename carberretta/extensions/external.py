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

import typing as t

from lightbulb import commands, context, decorators, plugins

if t.TYPE_CHECKING:
    from lightbulb.app import BotApp

plugin = plugins.Plugin("External")

LINKS: t.Final = (
    "Docs",
    "Donate",
    "GitHub",
    "Instagram",
    "LBRY",
    "Patreon",
    "Plans",
    "Twitch",
    "Twitter",
    "YouTube",
)


@plugin.command
@decorators.option("target", "The link to show.", choices=LINKS)
@decorators.command("link", "Retrieve a Carberra link.")
@decorators.implements(commands.slash.SlashCommand)
async def cmd_link(ctx: context.base.Context) -> None:
    await ctx.respond(f"<https://{ctx.options.target.lower()}.carberra.xyz>")


@plugin.command
@decorators.option("number", "The PEP number to search for.")
@decorators.command("pep", "Retrieve info on a Python Extension Protocol.")
@decorators.implements(commands.slash.SlashCommand)
async def cmd_pep(ctx: context.base.Context) -> None:
    n = ctx.options.number
    url = f"https://python.org/dev/peps/pep-{n:>04}"

    async with ctx.bot.d.session.get(url) as r:
        if not r.ok:
            await ctx.respond(f"PEP {n:>04} could not be found.")
            return

    await ctx.respond(f"PEP {n:>04}: <{url}>")


@plugin.command
@decorators.option("query", "The thing to search.")
@decorators.command("google", "Let me Google that for you...")
@decorators.implements(commands.slash.SlashCommand)
async def cmd_google(ctx: context.base.Context) -> None:
    q = ctx.options.query

    if len(q) > 500:
        await ctx.respond("Your query should be no longer than 500 characters.")
        return

    await ctx.respond(f"<https://letmegooglethat.com/?q={q.replace(' ', '+')}>")


@plugin.command
@decorators.option("query", "The thing to search.")
@decorators.command("duckduckgo", "Let me Duck Duck Go that for you...")
@decorators.implements(commands.slash.SlashCommand)
async def cmd_duckduckgo(ctx: context.base.Context) -> None:
    q = ctx.options.query

    if len(q) > 500:
        await ctx.respond("Your query should be no longer than 500 characters.")
        return

    await ctx.respond(f"<https://lmddgtfy.net/?q={q.replace(' ', '+')}>")


def load(bot: "BotApp") -> None:
    bot.add_plugin(plugin)


def unload(bot: "BotApp") -> None:
    bot.remove_plugin(plugin)
