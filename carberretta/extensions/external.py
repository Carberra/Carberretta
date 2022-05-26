# Copyright (c) 2020-present, Carberra Tutorials
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

import typing as t

import lightbulb

plugin = lightbulb.Plugin("External")

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
@lightbulb.option("target", "The link to show.", choices=LINKS)
@lightbulb.command("link", "Retrieve a Carberra link.")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_link(ctx: lightbulb.SlashContext) -> None:
    await ctx.respond(f"<https://{ctx.options.target.lower()}.carberra.xyz>")


@plugin.command
@lightbulb.option("number", "The PEP number to search for.")
@lightbulb.command("pep", "Retrieve info on a Python Extension Protocol.")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_pep(ctx: lightbulb.SlashContext) -> None:
    n = ctx.options.number
    url = f"https://python.org/dev/peps/pep-{n:>04}"

    async with ctx.bot.d.session.get(url) as r:
        if not r.ok:
            await ctx.respond(f"PEP {n:>04} could not be found.")
            return

    await ctx.respond(f"PEP {n:>04}: <{url}>")


@plugin.command
@lightbulb.option("query", "The thing to search.")
@lightbulb.command("google", "Let me Google that for you...")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_google(ctx: lightbulb.SlashContext) -> None:
    q = ctx.options.query

    if len(q) > 500:
        await ctx.respond("Your query should be no longer than 500 characters.")
        return

    await ctx.respond(f"<https://letmegooglethat.com/?q={q.replace(' ', '+')}>")


@plugin.command
@lightbulb.option("query", "The thing to search.")
@lightbulb.command("duckduckgo", "Let me Duck Duck Go that for you...")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_duckduckgo(ctx: lightbulb.SlashContext) -> None:
    q = ctx.options.query

    if len(q) > 500:
        await ctx.respond("Your query should be no longer than 500 characters.")
        return

    await ctx.respond(f"<https://lmddgtfy.net/?q={q.replace(' ', '+')}>")


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
