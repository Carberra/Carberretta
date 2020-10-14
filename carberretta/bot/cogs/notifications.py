"""
NOTIFICATIONS

Handles YouTube and Twitch notifications.
"""

import json
import os
import typing as t

import aiofiles
import aiofiles.os
import discord
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

from carberretta import Config
from carberretta.utils import DEFAULT_EMBED_COLOUR, chron

LIVE_EMBED_COLOUR = 0x9146FF
VOD_EMBED_COLOUR = 0x3498DB


class Notifications(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.notif_path = f"{bot._dynamic}/notifications.json"

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.videos_channel = self.bot.get_channel(Config.VIDEOS_ID)
            self.videos_role = self.bot.guild.get_role(Config.VIDEOS_ROLE_ID)
            self.streams_role = self.bot.guild.get_role(Config.STREAMS_ROLE_ID)

            # Imagine being able to use `setattr` here without mypy complaining.
            data = await self.load_states()
            self.last_video = data["last_video"]
            self.last_stream = data["last_stream"]
            self.last_vod = data["last_vod"]

            # Only enable the notification service on live bot.
            if (await self.bot.application_info()).id == 696804435321552906:
                self.bot.scheduler.add_job(self.check_for_videos, CronTrigger(hour="11,12", minute="2,5,15", second=0))

                self.bot.scheduler.add_job(
                    self.check_for_streams, CronTrigger(hour="12,13,14,15,20,21,22,23", minute="*/30", second=0),
                )

                self.bot.scheduler.add_job(self.check_for_vods, CronTrigger(hour="*/3", minute=0, second=0))

            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        data = {"last_video": self.last_video, "last_stream": self.last_stream, "last_vod": self.last_vod}

        await self.save_states(data)

    async def on_shutdown(self) -> None:
        data = {"last_video": self.last_video, "last_stream": self.last_stream, "last_vod": self.last_vod}

        await self.save_states(data)

    async def load_states(self) -> t.Mapping[str, str]:
        if os.path.isfile(self.notif_path):
            async with aiofiles.open(self.notif_path, "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
            await aiofiles.os.remove(self.notif_path)
            return data
        else:
            return {"last_video": "", "last_stream": "", "last_vod": ""}

    async def save_states(self, data: t.Mapping[str, str]) -> None:
        async with aiofiles.open(self.notif_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False))

    async def check_for_videos(self) -> None:
        url1 = f"https://www.googleapis.com/youtube/v3/search?type=video&order=date&channelId={Config.YOUTUBE_CHANNEL_ID}&key={Config.YOUTUBE_API_KEY}"

        async with self.bot.session.get(url1) as response:
            if response.status != 200:
                return

            if not (data := (await response.json())["items"]):
                return

        # Account for VODs appearing in this list.
        for item in data:
            latest_id = item["id"]["videoId"]
            url2 = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails%2CliveStreamingDetails%2Csnippet&id={latest_id}&key={Config.YOUTUBE_API_KEY}"

            async with self.bot.session.get(url2) as response:
                if response.status != 200:
                    return

                data = (await response.json())["items"][0]

            if "liveStreamingDetails" not in data.keys():
                break
        else:
            return

        if self.last_video == latest_id:
            return

        youtube = self.bot.get_cog("YouTube")

        await self.videos_channel.send(
            f"Hey {self.videos_role.mention}, a new video just went live! Come check it out!",
            embed=discord.Embed.from_dict(
                {
                    "title": data["snippet"]["title"],
                    "description": (
                        desc if len(desc := data["snippet"]["description"]) <= 500 else f"{desc[:500]}..."
                    ),
                    "color": DEFAULT_EMBED_COLOUR,
                    "url": f"https://youtube.com/watch?v={latest_id}",
                    "author": {"name": "Carberra Tutorials"},
                    "footer": {
                        "text": f"Duration: {youtube.get_duration(data['contentDetails']['duration'], long=True)}"
                    },
                    "image": {"url": data["snippet"]["thumbnails"]["maxres"]["url"]},
                }
            ),
        )

        self.last_video = latest_id
        return latest_id

    async def check_for_streams(self) -> None:
        url1 = f"https://www.googleapis.com/youtube/v3/search?type=video&event_type=live&order=date&maxResults=1&channelId={Config.YOUTUBE_CHANNEL_ID}&key={Config.YOUTUBE_API_KEY}"

        async with self.bot.session.get(url1) as response:
            if response.status != 200:
                return

            if not (data := (await response.json())["items"]):
                return

        latest_id = data[0]["id"]["videoId"]

        if self.last_stream == latest_id:
            return

        url2 = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails%2CliveStreamingDetails%2Csnippet&id={latest_id}&key={Config.YOUTUBE_API_KEY}"

        async with self.bot.session.get(url2) as response:
            if response.status != 200:
                return

            data = (await response.json())["items"][0]

        started_at = data["liveStreamingDetails"]["actualStartTime"][:-1]

        await self.videos_channel.send(
            f"Hey {self.streams_role.mention}, I'm live on YouTube now! Come watch!",
            embed=discord.Embed.from_dict(
                {
                    "title": data["snippet"]["title"],
                    "description": (
                        desc if len(desc := data["snippet"]["description"]) <= 500 else f"{desc[:500]}..."
                    ),
                    "color": LIVE_EMBED_COLOUR,
                    "url": f"https://youtube.com/watch?v={latest_id}",
                    "author": {"name": "Carberra Tutorials"},
                    "footer": {"text": f"Started {chron.long_date_and_time(chron.from_iso(started_at))} UTC"},
                    "image": {"url": data["snippet"]["thumbnails"]["maxres"]["url"]},
                }
            ),
        )

        self.last_stream = latest_id
        return latest_id

    async def check_for_vods(self) -> None:
        url1 = f"https://www.googleapis.com/youtube/v3/search?type=video&event_type=completed&order=date&maxResults=1&channelId={Config.YOUTUBE_CHANNEL_ID}&key={Config.YOUTUBE_API_KEY}"

        async with self.bot.session.get(url1) as response:
            if response.status != 200:
                return

            if not (data := (await response.json())["items"]):
                return

        latest_id = data[0]["id"]["videoId"]

        if self.last_vod == latest_id:
            return

        url2 = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails%2CliveStreamingDetails%2Csnippet&id={latest_id}&key={Config.YOUTUBE_API_KEY}"

        async with self.bot.session.get(url2) as response:
            if response.status != 200:
                return

            data = (await response.json())["items"][0]

        youtube = self.bot.get_cog("YouTube")

        await self.videos_channel.send(
            f"Hey {self.streams_role.mention}, a new VOD just went live! Catch up on anything you missed from the last stream!",
            embed=discord.Embed.from_dict(
                {
                    "title": data["snippet"]["title"],
                    "description": (
                        desc if len(desc := data["snippet"]["description"]) <= 500 else f"{desc[:500]}..."
                    ),
                    "color": VOD_EMBED_COLOUR,
                    "url": f"https://youtube.com/watch?v={latest_id}",
                    "author": {"name": "Carberra Tutorials"},
                    "footer": {
                        "text": f"Duration: {youtube.get_duration(data['contentDetails']['duration'], long=True)}"
                    },
                    "image": {"url": data["snippet"]["thumbnails"]["maxres"]["url"]},
                }
            ),
        )

        self.last_vod = latest_id
        return latest_id

    @commands.group(name="notify", invoke_without_command=True)
    @commands.is_owner()
    async def notify_group(self, ctx: commands.Context) -> None:
        pass

    @notify_group.command(name="video")
    @commands.is_owner()
    async def notify_video_command(self, ctx: commands.Context) -> None:
        last_video = await self.check_for_videos()
        await ctx.send(f"Announced video {last_video}.")

    @notify_group.command(name="stream")
    @commands.is_owner()
    async def notify_stream_command(self, ctx: commands.Context) -> None:
        last_stream = await self.check_for_streams()
        await ctx.send(f"Announced stream {last_stream}.")

    @notify_group.command(name="vod")
    @commands.is_owner()
    async def notify_vod_command(self, ctx: commands.Context) -> None:
        last_vod = await self.check_for_vods()
        await ctx.send(f"Announced VOD {last_vod}.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Notifications(bot))
