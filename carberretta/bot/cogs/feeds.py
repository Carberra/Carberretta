"""
FEEDS
Handles YouTube and Twitch feed notifications.
"""

import datetime as dt

import discord
import feedparser
from apscheduler.triggers.cron import CronTrigger
from discord.ext import commands

from carberretta import Config
from carberretta.utils import DEFAULT_EMBED_COLOUR, chron

LIVE_EMBED_COLOUR = 0x9146FF
VOD_EMBED_COLOUR = 0x3498DB


class Feeds(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def call_feed(self) -> dict:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={Config.YOUTUBE_CHANNEL_ID}&{dt.datetime.utcnow()}"
        async with self.bot.session.get(url) as response:
            if not 200 <= response.status <= 299:
                return []

            if not (data := feedparser.parse(await response.text()).entries):
                return []

        return data

    async def call_yt_api(self, video_id: str) -> dict:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails%2CliveStreamingDetails%2Csnippet&id={video_id}&key={Config.YOUTUBE_API_KEY}"
        async with self.bot.session.get(url) as response:
            if not 200 <= response.status <= 299:
                return []

            if not (data := await response.json()):
                return []

        return data["items"][0]

    async def call_twitch_api(self) -> dict:
        url = f"https://api.twitch.tv/helix/search/channels?query=carberratutorials"
        oauthurl = f"https://id.twitch.tv/oauth2/token?client_id={Config.TWITCH_CLIENT_ID}&client_secret={Config.TWITCH_CLIENT_SECRET}&grant_type=client_credentials"

        async with self.bot.session.post(url=oauthurl) as response:
            if not 200 <= response.status <= 299:
                return []

            if not (twitch_tok := (await response.json())["access_token"]):
                return []

        headers = {
            "client-id": f"{Config.TWITCH_CLIENT_ID}",
            "Authorization": f"Bearer {twitch_tok}",
        }

        async with self.bot.session.get(url=url, headers=headers) as response:
            if not 200 <= response.status <= 299:
                return []

            if not (data := await response.json()):
                return []

        return data["data"][0]

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.videos_channel = self.bot.get_channel(Config.VIDEOS_ID)
            self.videos_role = self.bot.guild.get_role(Config.VIDEOS_ROLE_ID)
            self.vods_role = self.bot.guild.get_role(Config.VODS_ROLE_ID)
            self.streams_role = self.bot.guild.get_role(Config.STREAMS_ROLE_ID)
            self.youtube = self.bot.get_cog("YouTube")

            if (await self.bot.application_info()).id == 696804435321552906:
                self.bot.scheduler.add_job(self.get_new_videos, CronTrigger(minute="*/3", second=0))
                self.bot.scheduler.add_job(self.get_new_vods, CronTrigger(minute="*/3", second=15))
                self.bot.scheduler.add_job(self.get_new_premieres, CronTrigger(minute="*/3", second=30))
                self.bot.scheduler.add_job(self.get_new_streams, CronTrigger(minute="*/3", second=45))

            self.bot.ready.up(self)

    async def get_new_vods(self) -> str:
        current_vod = await self.bot.db.field("SELECT ContentValue FROM feeds WHERE ContentType = ?", "vod")

        for item in await self.call_feed():
            data = await self.call_yt_api(item.yt_videoid)
            thumbnails = data["snippet"]["thumbnails"]
            duration = data["contentDetails"]["duration"]

            if current_vod == item.yt_videoid:
                # We announced this vod already
                return

            elif "#VOD" in item.summary:
                # This is a vod we havent announced

                await self.videos_channel.send(
                    f"Hey {self.vods_role.mention}, a new VOD just went live! Catch up on anything you missed from the last stream!",
                    embed=discord.Embed.from_dict(
                        {
                            "title": item.title,
                            "description": desc if len(desc := item.summary) <= 500 else f"{desc[:500]}...",
                            "color": VOD_EMBED_COLOUR,
                            "url": item.link,
                            "author": {"name": "Carberra Tutorials"},
                            "image": {"url": thumbnails["maxres"]["url"]},
                            "footer": {"text": f"Runtime: {self.youtube.get_duration(duration, long=True)}"},
                        }
                    ),
                )

                await self.bot.db.execute(
                    "UPDATE feeds SET ContentValue = ? WHERE ContentType = ?", item.yt_videoid, "vod"
                )

                await self.bot.db.commit()
                return item.yt_videoid

    async def get_new_videos(self) -> str:
        current_vid = await self.bot.db.field("SELECT ContentValue FROM feeds WHERE ContentType = ?", "video")

        for item in await self.call_feed():
            data = await self.call_yt_api(item.yt_videoid)
            thumbnails = data["snippet"]["thumbnails"]
            duration = data["contentDetails"]["duration"]

            if item.yt_videoid == current_vid:
                # This is a video we already announced
                return

            elif "liveStreamingDetails" not in data.keys():
                # A new video is live and its was not a premiere

                if "#VOD" not in item.summary:
                    # This isnt a VOD

                    await self.videos_channel.send(
                        f"Hey {self.videos_role.mention}, a new video just went live! Come check it out!",
                        embed=discord.Embed.from_dict(
                            {
                                "title": item.title,
                                "description": desc if len(desc := item.summary) <= 500 else f"{desc[:500]}...",
                                "color": DEFAULT_EMBED_COLOUR,
                                "url": item.link,
                                "author": {"name": "Carberra Tutorials"},
                                "image": {"url": thumbnails["maxres"]["url"]},
                                "footer": {"text": f"Runtime: {self.youtube.get_duration(duration, long=True)}"},
                            }
                        ),
                    )

                    await self.bot.db.execute(
                        "UPDATE feeds SET ContentValue = ? WHERE ContentType = ?", item.yt_videoid, "video"
                    )

                    await self.bot.db.commit()
                    return item.yt_videoid

    async def get_new_premieres(self) -> tuple:
        for item in await self.call_feed():
            data = await self.call_yt_api(item.yt_videoid)
            thumbnails = data["snippet"]["thumbnails"]
            duration = data["contentDetails"]["duration"]
            live_content = data["snippet"]["liveBroadcastContent"]

            upcoming = await self.bot.db.field(
                "SELECT Upcoming FROM premieres WHERE VideoID = ?", item.yt_videoid
            )

            announced = await self.bot.db.field(
                "SELECT Announced FROM premieres WHERE VideoID = ?", item.yt_videoid
            )

            if "liveStreamingDetails" in data.keys():
                start_time = data["liveStreamingDetails"]["scheduledStartTime"].strip("Z")
                scheduled_time = chron.from_iso(start_time)


                if not upcoming and duration != "P0D":
                    # We have not seen this premiere before

                    if live_content == "upcoming" and not announced:
                        # This premiere is upcoming and not live

                        await self.videos_channel.send(
                            f"Hey {self.videos_role.mention}, a new premiere is scheduled for {chron.long_date_and_time(scheduled_time)} UTC! Hope to see you there!",
                            embed=discord.Embed.from_dict(
                                {
                                    "title": item.title,
                                    "description": desc if len(desc := item.summary) <= 500 else f"{desc[:500]}...",
                                    "color": DEFAULT_EMBED_COLOUR,
                                    "url": item.link,
                                    "author": {"name": "Carberra Tutorials"},
                                    "image": {"url": thumbnails["maxres"]["url"]},
                                    "footer": {"text": f"Runtime: {self.youtube.get_duration(duration, long=True)}"},
                                }
                            ),
                        )

                        await self.bot.db.execute(
                            "REPLACE INTO premieres (VideoID, Upcoming, Announced) VALUES (?, ?, ?)", item.yt_videoid, 1, 0
                        )

                        await self.bot.db.commit()
                        return item.yt_videoid, False

                    elif live_content =="live" and not upcoming and not announced:
                        # The premiere was never upcoming is now live

                        await self.videos_channel.send(
                            f"Hey {self.videos_role.mention}, a new premiere started on {chron.long_date_and_time(scheduled_time)} UTC! Come and join us!",
                            embed=discord.Embed.from_dict(
                                {
                                    "title": item.title,
                                    "description": desc if len(desc := item.summary) <= 500 else f"{desc[:500]}...",
                                    "color": DEFAULT_EMBED_COLOUR,
                                    "url": item.link,
                                    "author": {"name": "Carberra Tutorials"},
                                    "image": {"url": thumbnails["maxres"]["url"]},
                                    "footer": {"text": f"Runtime: {self.youtube.get_duration(duration, long=True)}"},
                                }
                            ),
                        )

                        await self.bot.db.execute(
                            "REPLACE INTO premieres (VideoID, Upcoming, Announced) VALUES (?, ?, ?)", item.yt_videoid, 1, 1
                        )

                        await self.bot.db.commit()
                        return item.yt_videoid, True

                elif not announced:
                    # A premiere was upcoming, and is now live

                    await self.videos_channel.send(
                        f"Hey {self.videos_role.mention}, a new premiere started on {chron.long_date_and_time(scheduled_time)} UTC! Come and join us!",
                        embed=discord.Embed.from_dict(
                            {
                                "title": item.title,
                                "description": desc if len(desc := item.summary) <= 500 else f"{desc[:500]}...",
                                "color": DEFAULT_EMBED_COLOUR,
                                "url": item.link,
                                "author": {"name": "Carberra Tutorials"},
                                "image": {"url": thumbnails["maxres"]["url"]},
                                "footer": {"text": f"Runtime: {self.youtube.get_duration(duration, long=True)}"},
                            }
                        ),
                    )

                    await self.bot.db.execute(
                        "REPLACE INTO premieres (VideoID, Upcoming, Announced) VALUES (?, ?, ?)", item.yt_videoid, 1, 1
                    )

                    await self.bot.db.commit()
                    return item.yt_videoid, True

    async def get_new_streams(self) -> tuple:
        data = await self.call_twitch_api()

        if data:

            if data["is_live"] and not int(
                await self.bot.db.field("SELECT ContentValue FROM feeds WHERE ContentType = ?", "stream_live")
            ): # The stream is live and we havent announced it yet

                start = chron.from_iso(data["started_at"].strip("Z"))

                message = await self.videos_channel.send(
                    f"Hey {self.streams_role.mention}, I'm live on Twitch now! Come watch!",
                    embed=discord.Embed.from_dict(
                        {
                            "title": data["title"],
                            "description": f"**Category: {data['game_name']}**",
                            "color": LIVE_EMBED_COLOUR,
                            "url": "https://www.twitch.tv/carberratutorials",
                            "author": {"name": "Carberra Tutorials"},
                            "thumbnail": {"url": data["thumbnail_url"]},
                            "footer": {"text": f"Started: {chron.long_date_and_time(start)} UTC"},
                        }
                    ),
                )

                await self.bot.db.execute("UPDATE feeds SET ContentValue = '1' WHERE ContentType = ?", "stream_live")

                await self.bot.db.execute("UPDATE feeds SET ContentValue = ? WHERE ContentType = ?", start, "stream_start")

                await self.bot.db.execute(
                    "UPDATE feeds SET ContentValue = ? WHERE ContentType = ?", message.id, "stream_message"
                )

                await self.bot.db.commit()
                return data["title"], False

            elif not data["is_live"] and int(
                await self.bot.db.field("SELECT ContentValue FROM feeds WHERE ContentType = ?", "stream_live")
            ):
                # The stream is not live and last we checked it was (stream is over)

                await self.bot.db.execute("UPDATE feeds SET ContentValue = '0' WHERE ContentType = ?", "stream_live")

                await self.bot.db.execute(
                    "UPDATE feeds SET ContentValue = ? WHERE ContentType = ?", dt.datetime.utcnow(), "stream_end"
                )

                await self.bot.db.commit()

                duration = chron.from_iso(
                    await self.bot.db.field("SELECT ContentValue FROM feeds WHERE ContentType = ?", "stream_end")
                ) - chron.from_iso(
                    await self.bot.db.field("SELECT ContentValue FROM feeds WHERE ContentType = ?", "stream_start")
                )

                try:
                    message = await self.videos_channel.fetch_message(
                        int(
                            await self.bot.db.field(
                                "SELECT ContentValue FROM feeds WHERE ContentType = ?", "stream_message"
                            )
                        )
                    )

                except (discord.NotFound, discord.Forbidden, discord.HTTPException):
                    return

                else:
                    await message.edit(
                        content=f"Hey {self.streams_role.mention}, I'm live on Twitch now! Come watch!",
                        embed=discord.Embed.from_dict(
                            {
                                "title": "The stream has ended.",
                                "description": "**Catch you in the next one!**",
                                "color": LIVE_EMBED_COLOUR,
                                "url": "https://www.twitch.tv/carberratutorials",
                                "author": {"name": "Carberra Tutorials"},
                                "thumbnail": {"url": data["thumbnail_url"]},
                                "footer": {"text": f"Runtime: {chron.long_delta(duration)}"},
                            }
                        ),
                    )

                    return data["title"], True

    @commands.group(name="feed", invoke_without_command=True)
    @commands.is_owner()
    async def feed_group(self, ctx: commands.Context) -> None:
        pass

    @feed_group.command(name="video")
    @commands.is_owner()
    async def feed_video_command(self, ctx: commands.Context) -> None:
        last_video = await self.get_new_videos()
        await ctx.send(f"Announced video: {last_video}." if last_video else "No new videos.")

    @feed_group.command(name="vod")
    @commands.is_owner()
    async def feed_vod_command(self, ctx: commands.Context) -> None:
        last_vod = await self.get_new_vods()
        await ctx.send(f"Announced VOD: {last_vod}." if last_vod else "No new VODs.")

    @feed_group.command(name="premiere")
    @commands.is_owner()
    async def feed_premiere_command(self, ctx: commands.Context) -> None:
        if not (last_premiere := await self.get_new_premieres()):
            await ctx.send("No new premieres.")
        else:
            await ctx.send(
                f"Announced live premiere: {last_premiere[0]}." if last_premiere[1] else f"Announced upcoming premiere: {last_premiere[0]}."
            )

    @feed_group.command(name="stream")
    @commands.is_owner()
    async def feed_stream_command(self, ctx: commands.Context) -> None:
        if not (last_stream := await self.get_new_streams()):
            await ctx.send("No new streams.")
        else:
            await ctx.send(
                f"Stream ended: {last_stream[0]}." if last_stream[1] else f"Announced stream: {last_stream[0]}."
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Feeds(bot))
