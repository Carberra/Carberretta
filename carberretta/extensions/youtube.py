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
import typing as t

import hikari
import lightbulb
import rapidfuzz as rf
import scrapetube

from carberretta import Config

plugin = lightbulb.Plugin("YouTube", include_datastore=True)
log = logging.getLogger(__name__)


def _similarity(s1: str, s2: str, **_: t.Any) -> float:
    chars = len(s1)
    if not chars:
        return 1.0

    s1, s2 = s1.lower(), s2.lower()
    combo, max_combo = 0, 0
    word_starts = [0] + [i for i, l in enumerate(s1, start=1) if l == " "]

    for w in word_starts:
        for char in s2:
            if s1[w + combo] == char:
                combo += 1
                if (w + combo) == chars:
                    return 1.0
            else:
                max_combo = max(combo, max_combo)
                combo = 0

    return max_combo / chars


def _link_options(value: str) -> list[str]:
    return [
        res[0]
        for res in rf.process.extract(
            value,
            plugin.d.directory.keys(),
            scorer=_similarity,
            limit=10,
            score_cutoff=0.5,
        )
    ]


@plugin.listener(hikari.StartedEvent)
async def on_started(_: hikari.StartedEvent) -> None:
    # There is no way to get all videos directly from the API without
    # either (1) going through OAuth, or (2) brute forcing, with an
    # eventual cap on 500 results. Scraping isn't exactly ideal, but
    # it only happens once on startup, and it works, so...get meme'd.

    log.info("Searching for videos...")
    videos = scrapetube.get_channel(Config.YOUTUBE_CHANNEL_ID)

    log.info(f"Creating directory (this could take some time)...")
    plugin.d.directory = {v["title"]["runs"][0]["text"]: v["videoId"] for v in videos}
    log.info(f"Created directory of {len(plugin.d.directory)} videos")


@plugin.command
@lightbulb.command("youtube", "YouTube commands.")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def cmd_youtube(_: lightbulb.SlashContext) -> None:
    ...


@cmd_youtube.child
@lightbulb.option("title", "The title of the video.", autocomplete=True)
@lightbulb.command("link", "Link a video (use if directing someone to watch a video).")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd_youtube_link(ctx: lightbulb.SlashContext) -> None:
    video_id = plugin.d.directory[ctx.options.title]
    await ctx.respond(f"https://youtube.com/watch?v={video_id}")


@cmd_youtube_link.autocomplete("title")
async def cmd_youtube_link_autocomplete(
    opt: hikari.AutocompleteInteractionOption, _: hikari.AutocompleteInteraction
) -> list[str]:
    assert isinstance(opt.value, str)
    return _link_options(opt.value)


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
