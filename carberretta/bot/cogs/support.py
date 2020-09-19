"""
SUPPORT

Handles support channels.
Provides tag and message archiving funcionalities.
"""

import asyncio
import datetime as dt
import json
import os
import re
import typing as t
from enum import Enum
from os.path import isfile

import aiofiles
import aiofiles.os
import aiohttp
import discord
from discord.ext import commands

from carberretta import Config

INACTIVE_TIME: t.Final = 3600


class SupportState(Enum):
    UNAVAILABLE = 0
    OCCUPIED = 1
    AVAILABLE = 2


STATES: t.Final = {
    Config.UNAVAILABLE_SUPPORT_ID: SupportState.UNAVAILABLE,
    Config.OCCUPIED_SUPPORT_ID: SupportState.OCCUPIED,
    Config.AVAILABLE_SUPPORT_ID: SupportState.AVAILABLE,
}


class SupportChannel:
    def __init__(self, channel: discord.TextChannel, message: t.Optional[discord.Message] = None):
        self.channel = channel
        self.message = message
        self.get_channel = self.channel.guild.get_channel

    @property
    def id(self) -> int:
        return self.channel.id

    @property
    def state(self) -> SupportState:
        return STATES.get(self.channel.category.id, SupportState.UNAVAILABLE)

    @property
    def occupied_from(self) -> t.Optional[dt.datetime]:
        return getattr(self.message, "created_at", None)

    @property
    def client(self) -> discord.Member:
        return getattr(self.message, "author", None)

    async def send_to_available(self) -> None:
        self.message = None
        await self.channel.edit(
            category=self.channel.guild.get_channel(Config.AVAILABLE_SUPPORT_ID),
            reason="Support channel is now available.",
        )

    async def send_to_occupied(self, message: discord.Message) -> None:
        self.message = message
        await self.channel.edit(
            category=self.channel.guild.get_channel(Config.OCCUPIED_SUPPORT_ID),
            reason="Support channel is now occupied.",
        )
        await self.channel.send(f"This channel is now occupied by {self.client.mention}.")

    async def send_to_unavailable(self) -> None:
        self.message = None
        await self.channel.edit(
            category=self.channel.guild.get_channel(Config.UNAVAILABLE_SUPPORT_ID),
            reason="Support channel is now available.",
        )


class Support(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.state_path = f"{self.bot._dynamic}/support.json"
        self._channels: t.List[SupportChannel] = []

    @property
    def usable_channels(self) -> t.List[SupportChannel]:
        return [c for c in self._channels if c.state != SupportState.UNAVAILABLE]

    @property
    def max_channels(self) -> int:
        return min(max(4, len(self.helper_role.members)), 20)

    def idle_timeout(self, offset=0) -> dt.datetime:
        return dt.datetime.now() + dt.timedelta(seconds=INACTIVE_TIME + offset)

    async def load_states(self) -> dict:
        if isfile(self.state_path):
            async with aiofiles.open(f"{self.bot._dynamic}/support.json", "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
            await aiofiles.os.remove(self.state_path)
            return data
        else:
            return {}

    async def save_states(self, data: dict) -> None:
        async with aiofiles.open(f"{self.bot._dynamic}/support.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False))

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.available_category = self.bot.get_channel(Config.AVAILABLE_SUPPORT_ID)
            self.occupied_category = self.bot.get_channel(Config.OCCUPIED_SUPPORT_ID)
            self.unavailable_category = self.bot.get_channel(Config.UNAVAILABLE_SUPPORT_ID)
            self.redirect_channel = self.bot.get_channel(Config.REDIRECT_ID)
            self.staff_role = self.available_category.guild.get_role(Config.STAFF_ROLE_ID)
            self.helper_role = self.available_category.guild.get_role(Config.HELPER_ROLE_ID)

            data = await self.load_states()

            for channel in self.available_category.text_channels:
                self._channels.append(SupportChannel(channel))

            for channel in self.occupied_category.text_channels:
                self._channels.append(sc := SupportChannel(channel, await channel.fetch_message(data[f"{channel.id}"])))
                last_message = (await sc.channel.history(limit=1).flatten())[0]
                secs_since_activity = (dt.datetime.utcnow() - last_message.created_at).seconds
                if secs_since_activity > INACTIVE_TIME:
                    await sc.send_to_available()
                else:
                    await self.schedule(sc, -secs_since_activity)

            self.bot.ready.up(self)

    async def on_shutdown(self) -> None:
        data = {
            f"{sc.id}": getattr(sc.message, "id", None)
            for sc in self._channels
        }

        await self.save_states(data)

    @commands.Cog.listener()
    async def on_message(self, message) -> None:
        if self.bot.ready.support and not message.author.bot:
            if (sc := self.get_support_channel(message.channel)) is None:
                return

            if sc.state == SupportState.AVAILABLE:
                if (claimed := self.claimed_channel(message.author)) is not None and claimed is not message.channel:
                    await claimed.send(
                        f"{message.author.mention}, you're still occupying this channel. If you have further questions, ask them here."
                    )
                    await message.delete()
                else:
                    await sc.send_to_occupied(message)
                    await self.schedule(sc)
                    if not self.available_category.text_channels:
                        await self.update_available()
            else:
                await self.reschedule(sc)

    async def schedule(self, sc, offset=0) -> None:
        self.bot.scheduler.add_job(
            self.close, id=f"{sc.channel.id}", next_run_time=self.idle_timeout(offset), args=[sc]
        )

    async def reschedule(self, sc, offset=0) -> None:
        self.bot.scheduler.get_job(f"{sc.channel.id}").modify(next_run_time=self.idle_timeout(offset))

    async def close(self, sc):
        if len(self.usable_channels) > self.max_channels:
            await sc.send_to_unavailable()
        else:
            await sc.send_to_available()

    def get_support_channel(self, tc: discord.TextChannel) -> t.Optional[SupportChannel]:
        for sc in self._channels:
            if sc.channel == tc:
                return sc
        return None

    def claimed_channel(self, member: discord.Member) -> t.Optional[discord.TextChannel]:
        for channel in self._channels:
            if member == channel.client:
                return channel.channel
        return None

    async def try_get_available_channel(self) -> t.Optional[discord.TextChannel]:
        try:
            return self.available_category.text_channels[0]
        except IndexError:
            return await self.update_available()

    async def update_available(self) -> t.Optional[discord.TextChannel]:
        if len(self.usable_channels) < self.max_channels:
            try:
                await (tc := self.unavailable_category.text_channels[0]).edit(
                    category=self.available_category, reason="All support channels are occupied."
                )
                return tc
            except IndexError:
                tc = await self.available_category.create_text_channel(
                    f"support-{len(self._channels)+1}", reason="All support channels are occupied."
                )
                self._channels.append(SupportChannel(tc))
                return tc

        return None

    @commands.command(name="close")
    async def close_command(self, ctx):
        if (sc := self.get_support_channel(ctx.channel)) is None:
            await ctx.message.delete()
            await ctx.send(f"{ctx.author.mention}, this isn't a support channel.", delete_after=10)
        else:
            if not (ctx.author == sc.client or self.staff_role in ctx.author.roles):
                await ctx.send(f"{ctx.author.mention}, you can't close this support case.")
            else:
                if sc.client is not None:
                    client = f"{sc.client.display_name}'{'s' if not sc.client.display_name.endswith('s') else ''}"
                else:
                    client = "The"
                await sc.mark_as_available()
                await ctx.send(f"{client} support case was closed.")

    @commands.command(name="client")
    async def client_command(self, ctx):
        if (sc := self.get_support_channel(ctx.channel)) is None:
            await ctx.message.delete()
            await ctx.send(f"{ctx.author.mention}, this isn't a support channel.", delete_after=10)
        else:
            if sc.client is None:
                await ctx.send("A channel client could not be identified.")
            else:
                await ctx.send(f"This channel is currently claimed by {sc.client.display_name}.")

    @commands.command(name="redirect")
    async def redirect_command(self, ctx, target: discord.Member) -> None:
        if (sc := self.get_support_channel(ctx.channel)) is None:
            await ctx.message.delete()
            return await ctx.send(f"{ctx.author.mention}, this isn't a support channel.", delete_after=10)

        if not (ctx.author == sc.client or self.staff_role in ctx.author.roles):
            return await ctx.send(f"{ctx.author.mention}, you can't redirect that member.")

        if not (purged := await ctx.channel.purge(after=sc.message, check=lambda m: m.author == target)):
            return await ctx.send(f"{target.display_name} doesn't appear to have been here recently.")

        # Redirection valid:
        await ctx.message.delete()
        if (channel := await self.try_get_available_channel()) and (sc := self.get_support_channel(channel)):
            await sc.send_to_occupied(purged[0])
            await self.schedule(sc)
            await channel.send(
                f"You were redirected as the channel you attempted to open a support case in is already occupied."
            )

            async def culminate(messages) -> t.List[str]:
                big_message = "**Your previous messages:**"
                for message in reversed(messages):
                    content = f"`{message.created_at.strftime('%H:%M:%S')}`  {message.content}"
                    while (match := re.search(r"```[a-z]*\n([\s\S]*?)```", content)) is not None:
                        async with aiohttp.ClientSession() as session:
                            async with session.post("https://hastebin.com/documents", data=match.group(1)) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    content = content.replace(match.group(0), f"https://hastebin.com/{data['key']}")
                    big_message += f"​\n{content}"

                return [big_message[i : i + 2000] for i in range(0, len(big_message), 2000)]

            for message in await culminate(purged):
                await channel.send(message)

        else:
            await self.redirect_channel.send(
                f"{target.name}, you were redirected as the channel you attempted to open a support case in is already occupied. Unfortunely, there are no available support channels, so you will need to wait for a channel to become available."
            )

    @commands.command(name="call")
    @commands.cooldown(1, 21600, commands.BucketType.member)
    async def call_command(self, ctx):
        # Calls a specified role. Useful for preventing mention spamming.
        pass


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Support(bot))
