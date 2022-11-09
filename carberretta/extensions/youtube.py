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
import logging
import typing as t

import hikari
import isodate
import lightbulb
import rapidfuzz as rf
from apscheduler.triggers.cron import CronTrigger
from scrapetube.scrapetube import get_videos

from carberretta import Config
from carberretta.utils import chron, helpers

if t.TYPE_CHECKING:
    from aiohttp import ClientSession

plugin = lightbulb.Plugin("YouTube", include_datastore=True)
log = logging.getLogger(__name__)

BROWSE_ENDPOINT = "https://www.youtube.com/youtubei/v1/browse"
CHANNELS_URL = (
    "https://www.googleapis.com/youtube/v3/channels"
    "?part=brandingSettings%2Csnippet%2Cstatistics"
)
LIST_URL = "https://www.youtube.com/playlist?list="
MINE_URL = f"https://www.youtube.com/channel/{Config.YOUTUBE_CHANNEL_ID}"
PLAYLISTS_URL = (
    "https://www.googleapis.com/youtube/v3/playlists?part=contentDetails%2Csnippet"
)
VIDEOS_URL = (
    "https://www.googleapis.com/youtube/v3/videos"
    "?part=contentDetails%2Csnippet%2Cstatistics"
)
WATCH_URL = "https://www.youtube.com/watch?v="


def _similarity(s1: str, s2: str, **_: t.Any) -> float:
    if not s1:
        # This will always be empty before the user types any input, so
        # we should just display everything.
        return 1.0

    s1, s2 = s1.lower(), s2.lower()

    combo = 0
    max_combo = 0

    for char in s2:
        if char == s1[combo]:
            combo += 1
            if combo == len(s1):
                return 1.0

        else:
            combo = 0
            max_combo = max(combo, max_combo)

    return max_combo / len(s1)


def _compile_options(value: str, directory: dict[str, str]) -> list[str]:
    return [
        res[0]
        for res in rf.process.extract(
            value,
            directory.keys(),
            scorer=_similarity,
            processor=None,
            limit=25,
            score_cutoff=0.5,
        )
    ]


def _create_video_directory() -> None:
    url = f"{MINE_URL}/videos?view=0&sort=dd&flow=grid"
    items = get_videos(url, BROWSE_ENDPOINT, f"richItemRenderer", None, 1)

    plugin.d["video_directory"] = {
        (v := x["content"]["videoRenderer"])["title"]["runs"][0]["text"]: v["videoId"]
        for x in items
    }

    log.info(f"Updated video directory ({len(plugin.d['video_directory'])} videos)")


def _create_playlist_directory() -> None:
    url = f"{MINE_URL}/playlists?view=0&sort=dd&flow=grid"
    items = get_videos(url, BROWSE_ENDPOINT, f"gridPlaylistRenderer", None, 1)

    plugin.d["playlist_directory"] = {
        x["title"]["runs"][0]["text"]: x[f"playlistId"] for x in items
    }

    log.info(
        f"Updated playlist directory ({len(plugin.d['playlist_directory'])} playlists)"
    )


@plugin.listener(hikari.StartedEvent)
async def on_started(_: hikari.StartedEvent) -> None:
    log.warning("Video and playlist directories will not be immediately available")
    loop = asyncio.get_running_loop()

    plugin.d.video_directory = {}
    loop.run_in_executor(None, _create_video_directory)
    plugin.app.d.scheduler.add_job(
        _create_video_directory, CronTrigger(hour=12, minute=5, second=0)
    )

    plugin.d.playlist_directory = {}
    loop.run_in_executor(None, _create_playlist_directory)
    plugin.app.d.scheduler.add_job(
        _create_playlist_directory, CronTrigger(hour=0, minute=0, second=0)
    )


@plugin.command
@lightbulb.command("youtube", "YouTube commands.")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def cmd_youtube(_: lightbulb.SlashContext) -> None:
    ...


# VIDEO COMMANDS -------------------------------------------------------


@cmd_youtube.child
@lightbulb.command("video", "YouTube video commands.")
@lightbulb.implements(lightbulb.SlashSubGroup)
async def cmd_youtube_video(_: lightbulb.SlashContext) -> None:
    ...


@cmd_youtube_video.child
@lightbulb.option(
    "title", "The title of the video you want to link.", autocomplete=True
)
@lightbulb.command("link", "Link a video.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd_youtube_video_link(ctx: lightbulb.SlashContext) -> None:
    video_id = plugin.d.video_directory[ctx.options.title]
    await ctx.respond(WATCH_URL + video_id)


@cmd_youtube_video_link.autocomplete("title")
async def cmd_youtube_video_link_autocomplete(
    opt: hikari.AutocompleteInteractionOption, _: hikari.AutocompleteInteraction
) -> list[str]:
    assert isinstance(opt.value, str)
    return _compile_options(opt.value, plugin.d.video_directory)


@cmd_youtube_video.child
@lightbulb.option(
    "title",
    "The title of the video you want to view information about.",
    autocomplete=True,
)
@lightbulb.command("information", "View information about a video.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd_youtube_video_information(ctx: lightbulb.SlashContext) -> None:
    if not (member := ctx.member):
        return

    video_id = plugin.d.video_directory[ctx.options.title]
    url = VIDEOS_URL + f"&id={video_id}&key={Config.YOUTUBE_API_KEY}"
    session: ClientSession = plugin.app.d.session

    async with session.get(url) as resp:
        if not resp.ok:
            await ctx.respond(
                f"The YouTube Data API returned {resp.status}: {resp.reason}."
            )
            return

        data = (await resp.json())["items"][0]

    thumbnails: dict[str, dict[str, str]] = data["snippet"]["thumbnails"]
    published = int(isodate.parse_datetime(data["snippet"]["publishedAt"]).timestamp())

    await ctx.respond(
        hikari.Embed(
            title=ctx.options.title,
            description=data["snippet"]["description"].split("\n", maxsplit=1)[0],
            url=WATCH_URL + video_id,
            colour=helpers.choose_colour(),
            timestamp=chron.aware_now(),
        )
        .set_author(name="Video Information")
        .set_footer(f"Requested by {member.display_name}", icon=member.avatar_url)
        .set_image(
            thumbnails["maxres"]["url"]
            if "maxres" in thumbnails.keys()
            else thumbnails["high"]["url"]
        )
        .add_field("Views", f"{int(data['statistics']['viewCount']):,}", inline=True)
        .add_field("Likes", f"{int(data['statistics']['likeCount']):,}", inline=True)
        .add_field(
            "Comments", f"{int(data['statistics']['commentCount']):,}", inline=True
        )
        .add_field("Published", f"<t:{published}:R>", inline=True)
        .add_field(
            "Duration", chron.nat_delta(data["contentDetails"]["duration"]), inline=True
        )
        .add_field(
            "Subtitles",
            "Available" if data["contentDetails"]["caption"] else "Unavailable",
            inline=True,
        )
    )


@cmd_youtube_video_information.autocomplete("title")
async def cmd_youtube_video_information_autocomplete(
    opt: hikari.AutocompleteInteractionOption, _: hikari.AutocompleteInteraction
) -> list[str]:
    assert isinstance(opt.value, str)
    return _compile_options(opt.value, plugin.d.video_directory)


# PLAYLIST COMMANDS ----------------------------------------------------


@cmd_youtube.child
@lightbulb.command("playlist", "YouTube playlist commands.")
@lightbulb.implements(lightbulb.SlashSubGroup)
async def cmd_youtube_playlist(_: lightbulb.SlashContext) -> None:
    ...


@cmd_youtube_playlist.child
@lightbulb.option(
    "title", "The title of the playlist you want to link.", autocomplete=True
)
@lightbulb.command("link", "Link a playlist.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd_youtube_playlist_link(ctx: lightbulb.SlashContext) -> None:
    playlist_id = plugin.d.playlist_directory[ctx.options.title]
    await ctx.respond(LIST_URL + playlist_id)


@cmd_youtube_playlist_link.autocomplete("title")
async def cmd_youtube_playlist_link_autocomplete(
    opt: hikari.AutocompleteInteractionOption, _: hikari.AutocompleteInteraction
) -> list[str]:
    assert isinstance(opt.value, str)
    return _compile_options(opt.value, plugin.d.playlist_directory)


@cmd_youtube_playlist.child
@lightbulb.option(
    "title",
    "The title of the playlist you want to view information about.",
    autocomplete=True,
)
@lightbulb.command("information", "View information about a playlist.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd_youtube_playlist_information(ctx: lightbulb.SlashContext) -> None:
    if not (member := ctx.member):
        return

    playlist_id = plugin.d.playlist_directory[ctx.options.title]
    url = PLAYLISTS_URL + f"&id={playlist_id}&key={Config.YOUTUBE_API_KEY}"
    session: ClientSession = plugin.app.d.session

    async with session.get(url) as resp:
        if not resp.ok:
            await ctx.respond(
                f"The YouTube Data API returned {resp.status}: {resp.reason}."
            )
            return

        data = (await resp.json())["items"][0]

    thumbnails: dict[str, dict[str, str]] = data["snippet"]["thumbnails"]
    published = int(isodate.parse_datetime(data["snippet"]["publishedAt"]).timestamp())

    await ctx.respond(
        hikari.Embed(
            title=ctx.options.title,
            description=data["snippet"]["description"],
            url=LIST_URL + playlist_id,
            colour=helpers.choose_colour(),
            timestamp=chron.aware_now(),
        )
        .set_author(name="Playlist Information")
        .set_footer(f"Requested by {member.display_name}", icon=member.avatar_url)
        .set_image(
            thumbnails["maxres"]["url"]
            if "maxres" in thumbnails.keys()
            else thumbnails["high"]["url"]
        )
        .add_field("Videos", f"{data['contentDetails']['itemCount']:,}", inline=True)
        .add_field("Published", f"<t:{published}:R>", inline=True)
    )


@cmd_youtube_playlist_information.autocomplete("title")
async def cmd_youtube_playlist_information_autocomplete(
    opt: hikari.AutocompleteInteractionOption, _: hikari.AutocompleteInteraction
) -> list[str]:
    assert isinstance(opt.value, str)
    return _compile_options(opt.value, plugin.d.playlist_directory)


# CHANNEL COMMANDS -----------------------------------------------------


@cmd_youtube.child
@lightbulb.command("channel", "View information about the Carberra channel.")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def cmd_youtube_channel(ctx: lightbulb.SlashContext) -> None:
    if not (member := ctx.member):
        return

    url = CHANNELS_URL + f"&id={Config.YOUTUBE_CHANNEL_ID}&key={Config.YOUTUBE_API_KEY}"
    session: ClientSession = plugin.app.d.session

    async with session.get(url) as resp:
        if not resp.ok:
            await ctx.respond(
                f"The YouTube Data API returned {resp.status}: {resp.reason}."
            )
            return

        data = (await resp.json())["items"][0]

    latest_title, latest_id = (
        next(iter(plugin.d.video_directory.items()))
        if plugin.d.video_directory
        else ("Not available", "dQw4w9WgXcQ")
    )
    published = int(isodate.parse_datetime(data["snippet"]["publishedAt"]).timestamp())
    stats = data["statistics"]

    await ctx.respond(
        hikari.Embed(
            title="Carberra",
            description=data["brandingSettings"]["channel"]["description"],
            url=MINE_URL,
            colour=helpers.choose_colour(),
            timestamp=chron.aware_now(),
        )
        .set_author(name="Channel Information")
        .set_footer(f"Requested by {member.display_name}", icon=member.avatar_url)
        .set_thumbnail(data["snippet"]["thumbnails"]["high"]["url"])
        .set_image(data["brandingSettings"]["image"]["bannerExternalUrl"])
        .add_field("Subscribers", f"~{int(stats['subscriberCount']):,}", inline=True)
        .add_field("Views", f"{int(stats['viewCount']):,}", inline=True)
        .add_field("Videos", f"{int(stats['videoCount']):,}", inline=True)
        .add_field("Latest video", f"[{latest_title}]({WATCH_URL + latest_id})")
        .add_field("Created", f"<t:{published}:R>")
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
