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

import io
import logging
import re
import typing as t
import zlib
from dataclasses import dataclass

import hikari
import lightbulb
from apscheduler.triggers.cron import CronTrigger
from rapidfuzz import fuzz, process

from carberretta.utils import chron, helpers


@dataclass
class NamedCache:
    direct: str
    link: str
    type: str


if t.TYPE_CHECKING:
    CachedObjT = dict[str, NamedCache]

plugin = lightbulb.Plugin("RTFM", include_datastore=True)
CHUNK_REGEX: t.Final = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")
HIKARI_DOCS_URL: t.Final = "https://www.hikari-py.dev/"
LIGHTBULB_DOCS_URL: t.Final = "https://hikari-lightbulb.readthedocs.io/en/latest/"
PYTHON_DOCS_URL: t.Final = "https://docs.python.org/3/"

log = logging.getLogger(__name__)


async def refresh_rtfm_cache() -> None:
    hk = await plugin.bot.d.session.get(HIKARI_DOCS_URL + "objects.inv")
    plugin.bot.d.hikari_cache = decode_object_inv(await hk.read())

    lb = await plugin.bot.d.session.get(LIGHTBULB_DOCS_URL + "objects.inv")
    plugin.bot.d.lightbulb_cache = decode_object_inv(await lb.read())

    py = await plugin.bot.d.session.get(PYTHON_DOCS_URL + "objects.inv")
    plugin.bot.d.python_cache = decode_object_inv(await py.read())

    log.info(f"Refreshed all RTFM caches.")


@plugin.listener(hikari.StartedEvent)
async def on_started(_: hikari.StartedEvent) -> None:
    hk = await plugin.bot.d.session.get(HIKARI_DOCS_URL + "objects.inv")
    plugin.bot.d.hikari_cache = decode_object_inv(await hk.read())

    lb = await plugin.bot.d.session.get(LIGHTBULB_DOCS_URL + "objects.inv")
    plugin.bot.d.lightbulb_cache = decode_object_inv(await lb.read())

    plugin.app.d.scheduler.add_job(
        refresh_rtfm_cache, CronTrigger(hour="0,6,12,18", minute=0, second=0)
    )


async def get_rtfm(value: str, cache: CachedObjT) -> list[str]:
    extracted = process.extract(value, cache.keys(), scorer=fuzz.QRatio, limit=15)
    matches = []
    pure_matches = []
    for result, _, _ in extracted:
        if value in result:
            pure_matches.append(result)
        else:
            matches.append(result)
    return pure_matches + matches


async def build_rtfm_output(query: str, cache: CachedObjT, url: str) -> hikari.Embed:
    matches = await get_rtfm(query, cache)
    description = []

    for match in matches:
        if match in cache:
            if cache[match].link[-1:] == "$":
                description.append(
                    f"[`{match}`]({url}{cache[match].link[:-1] + cache[match].direct})"
                )
            else:
                description.append(f"[`{match}`]({url}{cache[match].link})")
    return hikari.Embed(
        title="RTFM",
        description="\n".join(description),
        color=helpers.choose_colour(),
        timestamp=chron.aware_now(),
    )


@plugin.command
@lightbulb.command(
    "rtfm", description="Searches the docs of hikari, lightbulb and python."
)
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
    embed = await build_rtfm_output(
        ctx.options.query, plugin.bot.d.hikari_cache, HIKARI_DOCS_URL
    )
    await ctx.respond(embed=embed)


@rtfm_group.child
@lightbulb.option("query", "The query to search for", autocomplete=True, required=True)
@lightbulb.command(
    "lightbulb", description="Searches the docs of lightbulb.", auto_defer=True
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def lightbulb_rtfm(ctx: lightbulb.SlashContext) -> None:
    embed = await build_rtfm_output(
        ctx.options.query, plugin.bot.d.lightbulb_cache, LIGHTBULB_DOCS_URL
    )
    await ctx.respond(embed=embed)


@rtfm_group.child
@lightbulb.option("query", "The query to search for", autocomplete=True, required=True)
@lightbulb.command(
    "python", description="Searches the docs of python.", auto_defer=True
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def python_rtfm(ctx: lightbulb.SlashContext) -> None:
    embed = await build_rtfm_output(
        ctx.options.query, plugin.bot.d.python_cache, PYTHON_DOCS_URL
    )
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


@python_rtfm.autocomplete("query")
async def python_autocomplete(
    opt: hikari.AutocompleteInteractionOption, _: hikari.AutocompleteInteraction
) -> list[str]:
    assert isinstance(opt.value, str)
    return await get_rtfm(opt.value, plugin.bot.d.python_cache)


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
        if not (match := CHUNK_REGEX.match(line.rstrip())):
            continue

        direct, type, _, link, _ = match.groups()
        if direct in cache:
            continue
        cache[direct] = NamedCache(direct, link, type)
    return cache


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
