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
import io
import re
import typing as t
import zlib

import hikari
import lightbulb
from rapidfuzz import fuzz, process

import carberretta
from carberretta.utils import helpers

if t.TYPE_CHECKING:
    CachedObjT = dict[str | t.Any, tuple[tuple[str | t.Any, ...], str | t.Any]]

plugin = lightbulb.Plugin("RTFM", include_datastore=True)
regex = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")


@plugin.listener(hikari.StartedEvent)
async def on_started(_: hikari.StartedEvent) -> None:
    hk = await plugin.bot.d.session.get(carberretta.HIKARI_DOCS_URL + "objects.inv")
    plugin.bot.d.hikari_cache = decode_object_inv(await hk.read())

    lb = await plugin.bot.d.session.get(carberretta.LIGHTBULB_DOCS_URL + "objects.inv")
    plugin.bot.d.lightbulb_cache = decode_object_inv(await lb.read())


@plugin.command
@lightbulb.command("rtfm", description="Searches the docs of hikari and lightbulb.")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def rtfm_group(_: lightbulb.SlashContext) -> None:
    pass


@rtfm_group.child
@lightbulb.option("query", "The query to search for", autocomplete=True, required=True)
@lightbulb.command(
    "hikari", description="Searches the docs of hikari.", auto_defer=True
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def hikari_rtfm(ctx: lightbulb.SlashContext) -> None:
    matches = await get_rtfm(ctx.options.query, plugin.bot.d.hikari_cache)
    embed = hikari.Embed(
        title="RTFM",
        color=helpers.choose_colour(),
        timestamp=dt.datetime.now().astimezone(),
    )
    embed.description = ""

    for match in matches:
        try:
            embed.description += (
                f"[`{match}`]({carberretta.HIKARI_DOCS_URL}"
                f"{plugin.bot.d.hikari_cache[match][1]})\n"
            )
        except:
            continue

    await ctx.respond(embed=embed)


@rtfm_group.child
@lightbulb.option("query", "The query to search for", autocomplete=True, required=True)
@lightbulb.command(
    "lightbulb", description="Searches the docs of lightbulb.", auto_defer=True
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def lightbulb_rtfm(ctx: lightbulb.SlashContext) -> None:
    matches = await get_rtfm(ctx.options.query, plugin.bot.d.lightbulb_cache)
    embed = hikari.Embed(
        title="RTFM",
        color=helpers.choose_colour(),
        timestamp=dt.datetime.now().astimezone(),
    )
    embed.description = ""

    for match in matches:
        try:
            embed.description += (
                f"[`{match}`]({carberretta.LIGHTBULB_DOCS_URL}"
                f"{plugin.bot.d.lightbulb_cache[match][1]})\n"
            )
        except:
            continue

    await ctx.respond(embed=embed)


@hikari_rtfm.autocomplete("query")
async def hikari_autocomplete(
    opt: hikari.AutocompleteInteractionOption, _: hikari.AutocompleteInteraction
) -> list[str]:
    assert isinstance(opt.value, str)
    return await get_rtfm(opt.value, plugin.bot.d.hikari_cache)


@lightbulb_rtfm.autocomplete("query")
async def lightbulb_autocomplete(
    opt: hikari.AutocompleteInteractionOption, _: hikari.AutocompleteInteraction
) -> list[str]:
    assert isinstance(opt.value, str)
    return await get_rtfm(opt.value, plugin.bot.d.lightbulb_cache)


async def get_rtfm(value: str, cache: dict[str, str]) -> list[str]:
    matches = process.extract(value, cache.keys(), scorer=fuzz.QRatio, limit=15)
    return [result for result, _, _ in matches]


def decode_object_inv(
    stream: bytes,
) -> CachedObjT:
    cache: CachedObjT = {}
    bytes_obj = io.BytesIO(stream)

    if bytes_obj.readline().decode("utf-8").rstrip() != "# Sphinx inventory version 2":
        raise RuntimeError("Invalid object inv version")

    # Skip over the projects name and version
    bytes_obj.readline()
    bytes_obj.readline()

    if "zlib" not in bytes_obj.readline().decode("utf-8"):
        raise RuntimeError("Invalid object.inv file")

    def decompress_chunks(bytes_obj: io.BytesIO) -> t.Generator[str, None, None]:
        def decompress(bytes_obj: io.BytesIO) -> t.Generator[bytes, None, None]:
            decompressor = zlib.decompressobj()

            for chunk in bytes_obj:
                yield decompressor.decompress(chunk)

            yield decompressor.flush()

        cache = b""
        for chunk in decompress(bytes_obj):
            cache += chunk
            pos = cache.find(b"\n")

            while pos != -1:
                yield cache[:pos].decode("utf-8")
                cache = cache[pos + 1 :]
                pos = cache.find(b"\n")

    for line in decompress_chunks(bytes_obj):
        if not (match := regex.match(line.rstrip())):
            continue

        if match in cache:
            continue

        direct, _, _, link, _ = match.groups()
        cache[direct] = (match.groups(), link)

    return cache


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
