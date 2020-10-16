"""
YOUTUBE

Handles YouTube content notifications and stats.
"""

import datetime as dt
import json
import os
import re
import typing as t

import aiofiles
import aiofiles.os
import aiohttp
import discord
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

from carberretta import Config
from carberretta.utils import DEFAULT_EMBED_COLOUR, chron, menu


class SearchMenu(menu.NumberedSelectionMenu):
    def __init__(self, ctx, data, results, pagemap):
        self.data = data
        super().__init__(ctx, results, pagemap)

    async def start(self):
        if (r := await super().start()) is not None:
            await self.display_video(r)

    async def display_video(self, name):
        for item in self.data["items"]:
            if item["snippet"]["title"] == name:
                url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails%2Csnippet%2Cstatistics&id={item['id']['videoId']}&key={Config.YOUTUBE_API_KEY}"

                await self.message.clear_reactions()

                async with self.ctx.bot.session.get(url) as response:
                    if response.status != 200:
                        return await self.message.edit(
                            content=f"The YouTube API returned {response.status} {response.reason}.", embed=None
                        )

                    data = (await response.json())["items"][0]

                youtube = self.ctx.bot.get_cog("YouTube")
                duration = youtube.get_duration(data["contentDetails"]["duration"])
                published_at = chron.from_iso(data["snippet"]["publishedAt"][:-1])

                await self.message.edit(
                    embed=discord.Embed.from_dict(
                        {
                            "title": item["snippet"]["title"],
                            "description": f"Click [here](https://youtube.com/watch?v={item['id']['videoId']}) to watch. Use `{Config.PREFIX}yt video {item['id']['videoId']}` for detailed video information.",
                            "color": DEFAULT_EMBED_COLOUR,
                            "author": {"name": "Query"},
                            "footer": {
                                "text": f"Requested by {self.ctx.author.display_name} • {youtube.searches_today}/50",
                                "icon_url": f"{self.ctx.author.avatar_url}",
                            },
                            "fields": [
                                {"name": "Published on", "value": f"{chron.long_date(published_at)}", "inline": True},
                                {"name": "Duration", "value": duration, "inline": True},
                                {
                                    "name": "Views",
                                    "value": f"{int(data['statistics']['viewCount']):,}",
                                    "inline": True,
                                },
                            ],
                        }
                    )
                )


class YouTube(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.yt_path = f"{bot._dynamic}/yt.json"

        bot.scheduler.add_job(self._reset_search_cap, CronTrigger(hour=0, minute=0, second=0))

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            data = await self.load_states()
            self.searches_today = data["searches_today"]

            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        data = {"searches_today": self.searches_today}

        await self.save_states(data)

    async def on_shutdown(self) -> None:
        data = {"searches_today": self.searches_today}

        await self.save_states(data)

    async def load_states(self) -> t.Mapping[str, int]:
        if os.path.isfile(self.yt_path):
            async with aiofiles.open(self.yt_path, "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
            await aiofiles.os.remove(self.yt_path)
            return data
        else:
            return {"searches_today": 0}

    async def save_states(self, data: t.Mapping[str, int]) -> None:
        async with aiofiles.open(self.yt_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False))

    def _reset_search_cap(self) -> None:
        self.searches_today = 0

    def get_duration(self, duration, long=False):
        if (
            match := re.match(r"PT(([0-9]{1,})D)?(([0-9]{1,2})H)?(([0-9]{1,2})M)?(([0-9]{1,2})S)?", duration)
        ) is not None:
            delta_func = chron.long_delta if long else chron.short_delta
            return delta_func(
                dt.timedelta(
                    seconds=(int(match.group(2) or 0) * 86400)
                    + (int(match.group(4) or 0) * 3600)
                    + (int(match.group(6) or 0) * 60)
                    + (int(match.group(8) or 0))
                )
            )
        else:
            return "-"

    @commands.group(name="yt", invoke_without_command=True)
    async def yt_group(self, ctx: commands.Context) -> None:
        await ctx.send("Use `yt stats`, `yt info`, `yt search`, or `yt video`.")

    @yt_group.command(name="stats")
    async def yt_stats_command(self, ctx: commands.Context) -> None:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=snippet%2Cstatistics&id={Config.YOUTUBE_CHANNEL_ID}&key={Config.YOUTUBE_API_KEY}"

        async with ctx.typing():
            async with self.bot.session.get(url) as response:
                if response.status != 200:
                    return await ctx.send(f"The YouTube API returned {response.status} {response.reason}.")

                data = (await response.json())["items"][0]

            sub_count = int(data["statistics"]["subscriberCount"])

            await ctx.send(
                embed=discord.Embed.from_dict(
                    {
                        "title": f"Channel statistics for {data['snippet']['title']}",
                        "color": DEFAULT_EMBED_COLOUR,
                        "thumbnail": {"url": data["snippet"]["thumbnails"]["high"]["url"]},
                        "author": {"name": "Information"},
                        "footer": {
                            "text": f"Requested by {ctx.author.display_name}",
                            "icon_url": f"{ctx.author.avatar_url}",
                        },
                        "fields": [
                            {"name": "Subscribers", "value": f"About {sub_count:,}", "inline": False},
                            {"name": "Views", "value": f"{int(data['statistics']['viewCount']):,}", "inline": False},
                            {"name": "Videos", "value": f"{int(data['statistics']['videoCount']):,}", "inline": False},
                        ],
                    }
                )
            )

    @yt_group.command(name="info")
    async def yt_info_command(self, ctx: commands.Context) -> None:
        url = f"https://www.googleapis.com/youtube/v3/channels?part=brandingSettings%2Csnippet%2Cstatistics&id={Config.YOUTUBE_CHANNEL_ID}&key={Config.YOUTUBE_API_KEY}"

        async with ctx.typing():
            async with self.bot.session.get(url) as response:
                if response.status != 200:
                    return await ctx.send(f"The YouTube API returned {response.status} {response.reason}.")

                data = (await response.json())["items"][0]

            published_at = chron.from_iso(data["snippet"]["publishedAt"][:-1])

            await ctx.send(
                embed=discord.Embed.from_dict(
                    {
                        "title": f"Channel information for {data['brandingSettings']['channel']['title']}",
                        "description": data["brandingSettings"]["channel"]["description"],
                        "color": DEFAULT_EMBED_COLOUR,
                        "thumbnail": {"url": data["snippet"]["thumbnails"]["high"]["url"]},
                        "image": {"url": data["brandingSettings"]["image"]["bannerTvImageUrl"]},
                        "author": {"name": "Information"},
                        "footer": {
                            "text": f"Requested by {ctx.author.display_name}",
                            "icon_url": f"{ctx.author.avatar_url}",
                        },
                        "fields": [
                            {
                                "name": "Trailer",
                                "value": f"Click [here](https://www.youtube.com/watch?v={data['brandingSettings']['channel']['unsubscribedTrailer']}) to watch.",
                                "inline": False,
                            },
                            {
                                "name": "Country",
                                "value": data["brandingSettings"]["channel"]["country"],
                                "inline": False,
                            },
                            {
                                "name": "Published on",
                                "value": f"{chron.long_date_and_time(published_at)} UTC",
                                "inline": False,
                            },
                            {
                                "name": "Existed for",
                                "value": chron.long_delta(dt.datetime.utcnow() - published_at),
                                "inline": False,
                            },
                        ],
                    }
                )
            )

    @yt_group.command(name="search")
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def yt_search_command(self, ctx: commands.Context, *, query: str) -> None:
        if self.searches_today >= 50:
            return await ctx.send("Reached maximum amount of daily searches (50).")

        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={query}&type=video&maxResults=50&channelId={Config.YOUTUBE_CHANNEL_ID}&key={Config.YOUTUBE_API_KEY}"

        async with ctx.typing():
            async with self.bot.session.get(url) as response:
                self.searches_today += 1
                if response.status != 200:
                    return await ctx.send(f"The YouTube API returned {response.status} {response.reason}.")

                data = await response.json()

        pagemap = {
            "title": "Search results",
            "description": f"{data['pageInfo']['totalResults']} result(s).",
            "color": DEFAULT_EMBED_COLOUR,
            "author": {"name": "Query"},
            "footer": {
                "text": f"Requested by {ctx.author.display_name} • {self.searches_today}/50",
                "icon_url": f"{ctx.author.avatar_url}",
            },
        }
        results = [f"{item['snippet']['title']}" for item in data["items"]]

        if not results:
            return await ctx.send("No results found. Are you sure Carberra made a video on that?")

        await SearchMenu(ctx, data, results, pagemap).start()

    @yt_group.command(name="video")
    async def yt_video_command(self, ctx: commands.Context, id_: str) -> None:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails%2CliveStreamingDetails%2Csnippet%2Cstatistics&id={id_}&key={Config.YOUTUBE_API_KEY}"

        async with ctx.typing():
            async with self.bot.session.get(url) as response:
                if response.status != 200:
                    return await ctx.send(f"The YouTube API returned {response.status} {response.reason}.")

                if not (data := (await response.json())["items"]):
                    return await ctx.send("Invalid video ID.")

                data = data[0]

            if data["snippet"]["channelId"] != Config.YOUTUBE_CHANNEL_ID:
                return await ctx.send("That is not a Carberra video.")

            if (stream := "liveStreamingDetails" in data.keys()) :
                published_at = chron.from_iso(data["liveStreamingDetails"]["actualStartTime"][:-1])
            else:
                published_at = chron.from_iso(data["snippet"]["publishedAt"][:-1])
            duration = self.get_duration(data["contentDetails"]["duration"])

            await ctx.send(
                embed=discord.Embed.from_dict(
                    {
                        "title": "Video information",
                        "description": f"{data['snippet']['title']}. Click [here](https://youtube.com/watch?v={data['id']}) to watch.",
                        "color": DEFAULT_EMBED_COLOUR,
                        "author": {"name": "Information"},
                        "footer": {
                            "text": f"Requested by {ctx.author.display_name}",
                            "icon_url": f"{ctx.author.avatar_url}",
                        },
                        "image": {"url": data["snippet"]["thumbnails"]["maxres"]["url"]},
                        "fields": [
                            {"name": "Duration", "value": duration, "inline": True},
                            {"name": "Views", "value": f"{int(data['statistics']['viewCount']):,}", "inline": True},
                            {
                                "name": "Likes / dislikes",
                                "value": f"{int(data['statistics']['likeCount']):,} / {int(data['statistics']['dislikeCount']):,}",
                                "inline": True,
                            },
                            {
                                "name": "Comments",
                                "value": f"{int(data['statistics']['commentCount']):,}",
                                "inline": True,
                            },
                            {
                                "name": "Favourites",
                                "value": f"{int(data['statistics']['favoriteCount']):,}",
                                "inline": True,
                            },
                            {"name": "Tags", "value": len(data["snippet"]["tags"]), "inline": True},
                            {"name": "Stream?", "value": "liveStreamingDetails" in data.keys(), "inline": True,},
                            {"name": "Published on", "value": f"{chron.long_date(published_at)}", "inline": True},
                            {
                                "name": "Existed for",
                                "value": chron.short_delta(dt.datetime.utcnow() - published_at),
                                "inline": True,
                            },
                        ],
                    }
                )
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(YouTube(bot))
