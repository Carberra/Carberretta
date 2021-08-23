"""
SUPPORT

Handles support channels.
Provides tag and message archiving funcionalities.
"""

import asyncio
import datetime as dt
import io
import json
import os
import re
import typing as t
from enum import Enum
from inspect import Parameter

import aiofiles
import aiofiles.os
import aiohttp
import discord
from apscheduler.jobstores.base import ConflictingIdError
from discord.ext import commands

from carberretta import Config
from carberretta.utils import string

INACTIVE_TIME: t.Final = 3600
NAMES: t.Final = [
    "alpha",
    "beta",
    "gamma",
    "delta",
    "epsilon",
    "zeta",
    "eta",
    "theta",
    "iota",
    "kappa",
    "lambda",
    "mu",
    "nu",
    "xi",
    "omicron",
    "pi",
    "rho",
    "sigma",
    "tau",
    "upsilon",
    "phi",
    "chi",
    "psi",
    "omega",
]


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
        self._message = message
        self._previous_message = None
        self.get_channel = self.channel.guild.get_channel

    @property
    def id(self) -> int:
        return self.channel.id

    @property
    def state(self) -> SupportState:
        return STATES.get(self.channel.category.id, SupportState.UNAVAILABLE)

    @property
    def message(self) -> discord.Message:
        return self._message

    @message.setter
    def message(self, value: discord.Message) -> None:
        self._previous_message = self._message
        self._message = value

    @property
    def previous_message(self) -> discord.Message:
        return self._previous_message

    @property
    def occupied_from(self) -> t.Optional[dt.datetime]:
        return getattr(self.message, "created_at", None)

    @property
    def claimant(self) -> discord.Member:
        return getattr(self.message, "author", None)

    def determine_position_in(self, category: discord.CategoryChannel) -> int:
        return sorted([self.channel, *category.text_channels], key=lambda c: c.id).index(self.channel) + 1

    async def send_to_available(self) -> None:
        self.message = None
        category = self.channel.guild.get_channel(Config.AVAILABLE_SUPPORT_ID)
        await self.channel.edit(
            category=category,
            reason="Support channel is now available.",
            sync_permissions=True,
            position=self.determine_position_in(category),
        )

    async def send_to_occupied(self, message: discord.Message) -> None:
        self.message = message
        category = self.channel.guild.get_channel(Config.OCCUPIED_SUPPORT_ID)
        await self.channel.edit(
            category=category,
            reason="Support channel is now occupied.",
            sync_permissions=True,
            position=self.determine_position_in(category),
        )
        try:
            await self.channel.send(f"This channel is now occupied by {self.claimant.mention}.")
        except AttributeError:
            # Accounting for Kelsier's blasted macro d:
            pass

    async def send_to_unavailable(self) -> None:
        self.message = None
        category = self.channel.guild.get_channel(Config.UNAVAILABLE_SUPPORT_ID)
        await self.channel.edit(
            category=category,
            reason="Support channel is now unavailable.",
            sync_permissions=True,
            position=self.determine_position_in(category),
        )


class Support(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.state_path = f"{self.bot._dynamic}/support.json"
        self._channels: t.List[SupportChannel] = []

    @property
    def available_channels(self) -> t.List[SupportChannel]:
        return [c for c in self._channels if c.state == SupportState.AVAILABLE]

    @property
    def occupied_channels(self) -> t.List[SupportChannel]:
        return [c for c in self._channels if c.state == SupportState.OCCUPIED]

    @property
    def usable_channels(self) -> t.List[SupportChannel]:
        return [c for c in self._channels if c.state != SupportState.UNAVAILABLE]

    @property
    def max_total(self) -> int:
        return min(max(4, len(self.helper_role.members)), 24)

    @property
    def max_usable(self) -> int:
        return max(4, len([m for m in self.helper_role.members if m.status != discord.Status.offline]))

    @staticmethod
    def idle_timeout(offset: int = 0) -> dt.datetime:
        return dt.datetime.utcnow() + dt.timedelta(seconds=INACTIVE_TIME + offset)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.available_category = self.bot.get_channel(Config.AVAILABLE_SUPPORT_ID)
            self.occupied_category = self.bot.get_channel(Config.OCCUPIED_SUPPORT_ID)
            self.unavailable_category = self.bot.get_channel(Config.UNAVAILABLE_SUPPORT_ID)
            self.redirect_channel = self.bot.get_channel(Config.REDIRECT_ID)
            self.info_channel = self.bot.get_channel(Config.INFO_ID)
            self.staff_role = self.available_category.guild.get_role(Config.STAFF_ROLE_ID)
            self.helper_role = self.available_category.guild.get_role(Config.HELPER_ROLE_ID)

            data = await self.load_states()

            for channel in [*self.available_category.text_channels, *self.unavailable_category.text_channels]:
                self._channels.append(SupportChannel(channel))

            for channel in self.occupied_category.text_channels:
                try:
                    message = await channel.fetch_message(data[f"{channel.id}"])
                except discord.NotFound:
                    message = await channel.history(
                        limit=None, after=dt.datetime.utcnow() - dt.timedelta(seconds=7200)
                    ).get(author__id=self.bot.user.id)
                self._channels.append(sc := SupportChannel(channel, message))
                if message is None:
                    return await self.determine_channel_destination(sc)
                last_message = (await sc.channel.history(limit=1).flatten())[0]
                secs_since_activity = (dt.datetime.utcnow() - last_message.created_at).seconds
                if secs_since_activity > INACTIVE_TIME:
                    await self.determine_channel_destination(sc)
                else:
                    await self.schedule(sc, -secs_since_activity)

            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_disconnect(self) -> None:
        data = {f"{sc.id}": getattr(sc.message, "id", 0) for sc in self._channels}

        await self.save_states(data)

    async def on_shutdown(self) -> None:
        data = {f"{sc.id}": getattr(sc.message, "id", 0) for sc in self._channels}

        await self.save_states(data)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if self.bot.ready.support and not message.author.bot:
            if (sc := self.get_support_channel(message.channel)) is None or message.content.startswith(Config.PREFIX):
                return

            if sc.state == SupportState.AVAILABLE:
                if (
                    claimed := self.get_claimed_channel(message.author)
                ) is not None and claimed is not message.channel:
                    await claimed.send(
                        f"{message.author.mention}, you're still occupying this channel. If you have further questions, ask them here."
                    )
                    try:
                        await message.delete()
                    except discord.NotFound:
                        pass
                else:
                    await self.open_case(sc, message)
            else:
                await self.reschedule(sc)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if self.bot.ready.support:
            if (
                self.helper_role in after.roles
                and before.status != after.status
                and after.status == discord.Status.online
                and len(self.usable_channels) < self.max_usable
            ):
                await self.try_get_from_unavailable("Helper came online.")

            # Attempt to avoid caching problems.
            if before.roles != after.roles and (set(after.roles) ^ set(before.roles)).pop() == self.helper_role:
                self.helper_role = discord.utils.get(await self.bot.guild.fetch_roles(), id=Config.HELPER_ROLE_ID)

    async def open_case(self, sc: SupportChannel, message: discord.Message) -> None:
        await sc.send_to_occupied(message)
        await self.schedule(sc)
        if not self.available_category.text_channels:
            await self.update_available()

    async def schedule(self, sc: SupportChannel, offset: int = 0) -> None:
        try:
            self.bot.scheduler.add_job(
                self.close_case, id=f"{sc.channel.id}", next_run_time=self.idle_timeout(offset), args=[sc]
            )
        except ConflictingIdError:
            await self.reschedule(sc, offset)

    async def reschedule(self, sc: SupportChannel, offset: int = 0) -> None:
        try:
            self.bot.scheduler.get_job(f"{sc.channel.id}").modify(next_run_time=self.idle_timeout(offset))
        except AttributeError:
            pass

    async def unschedule(self, sc: SupportChannel) -> None:
        try:
            self.bot.scheduler.get_job(f"{sc.channel.id}").remove()
        except AttributeError:
            pass

    async def close_case(self, sc: SupportChannel) -> None:
        if sc.claimant == self.bot.user or sc.claimant == None:
            claimant = "The"
        else:
            claimant = f"{sc.claimant.display_name}'{'s' if not sc.claimant.display_name.endswith('s') else ''}"
        await self.determine_channel_destination(sc)
        await sc.channel.send(f"{claimant} support case timed out.")

    async def load_states(self) -> t.Mapping[str, int]:
        if os.path.isfile(self.state_path):
            async with aiofiles.open(f"{self.bot._dynamic}/support.json", "r", encoding="utf-8") as f:
                data = json.loads(await f.read())
            await aiofiles.os.remove(self.state_path)
            return data
        else:
            return {}

    async def save_states(self, data: t.Mapping[str, int]) -> None:
        async with aiofiles.open(f"{self.bot._dynamic}/support.json", "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False))

    def get_support_channel(self, tc: discord.TextChannel) -> t.Optional[SupportChannel]:
        for sc in self._channels:
            if sc.channel == tc:
                return sc
        return None

    def get_claimed_channel(self, member: discord.Member) -> t.Optional[discord.TextChannel]:
        for channel in self._channels:
            if member == channel.claimant:
                return channel.channel
        return None

    async def try_get_available_channel(self) -> t.Optional[discord.TextChannel]:
        try:
            return self.available_category.text_channels[0]
        except IndexError:
            return await self.update_available()

    async def try_get_from_unavailable(self, reason: str) -> t.Optional[discord.TextChannel]:
        try:
            await (tc := self.unavailable_category.text_channels[0]).edit(
                category=self.available_category, reason=reason, sync_permissions=True
            )
            return tc
        except IndexError:
            return None

    async def try_create_new_channel(self, reason: str) -> t.Optional[discord.TextChannel]:
        if len(self._channels) < self.max_total:
            tc = await self.available_category.create_text_channel(
                f"support-{NAMES[len(self._channels)]}",
                topic=f"Need help? Ask your question here. Read {self.info_channel.mention} for more information.",
                reason=reason,
            )
            self._channels.append(SupportChannel(tc))
            return tc

        return None

    async def determine_channel_destination(self, sc: SupportChannel) -> None:
        if len(self.usable_channels) > self.max_usable:
            return await sc.send_to_unavailable()

        await sc.send_to_available()

    async def update_available(self) -> t.Optional[discord.TextChannel]:
        if len(self.usable_channels) < self.max_usable:
            reason = "All usable support channels are occupied."
            return await self.try_get_from_unavailable(reason) or await self.try_create_new_channel(reason)

        return None

    @commands.command(name="close")
    async def close_command(self, ctx: commands.Context) -> None:
        if (sc := self.get_support_channel(ctx.channel)) is None:
            return await ctx.message.delete()

        if not (ctx.author == sc.claimant or self.staff_role in ctx.author.roles):
            return await ctx.send(f"{ctx.author.mention}, you can't close this support case.")

        if sc.claimant == self.bot.user or sc.claimant == None:
            claimant = "The"
        else:
            claimant = string.possessive(sc.claimant)
        await self.determine_channel_destination(sc)
        await self.unschedule(sc)
        await ctx.send(f"{claimant} support case was closed.")

    @commands.command(name="reopen")
    async def reopen_command(self, ctx: commands.Context, target: t.Optional[discord.Member]) -> None:
        if (sc := self.get_support_channel(ctx.channel)) is None:
            return await ctx.message.delete()

        if sc.state == SupportState.OCCUPIED:
            return await ctx.send("There is already a support case open in this channel.")

        if target is not None:
            message = await ctx.channel.history(
                limit=None, after=dt.datetime.utcnow() - dt.timedelta(seconds=86400),
            ).get(author__id=target.id)
        else:
            message = sc.previous_message

        if message is None:
            return await ctx.send("No case could be reopened.")

        await self.open_case(sc, message)

    @commands.command(name="claimant", aliases=["client"])
    async def claimant_command(self, ctx: commands.Context) -> None:
        if (sc := self.get_support_channel(ctx.channel)) is None:
            return await ctx.message.delete()

        if sc.claimant == self.bot.user:
            return await ctx.send("A channel claimant could not be identified.")

        await ctx.send(f"This channel is currently claimed by {sc.claimant.display_name}.")

    @commands.command(name="redirect")
    async def redirect_command(self, ctx: commands.Context, target: discord.Member) -> None:
        await ctx.message.delete()

        if (sc := self.get_support_channel(ctx.channel)) is None:
            return

        if sc.state == SupportState.AVAILABLE:
            return

        if not (ctx.author == sc.claimant or self.staff_role in ctx.author.roles):
            return await ctx.send(
                f"{ctx.author.mention}, you can't redirect members in this support case.", delete_after=10
            )

        if target == sc.claimant or target.bot:
            return await ctx.send(f"{ctx.author.mention}, that member can't be redirected.", delete_after=10)

        if not (purged := await ctx.channel.purge(after=sc.message, check=lambda m: m.author == target)):
            return await ctx.send(f"{target.display_name} doesn't appear to have been here recently.", delete_after=10)

        # Redirection valid:
        async def culminate(messages) -> t.List[str]:
            big_message = "**Your previous messages:**"
            for message in reversed(messages):
                content = f"`{message.created_at.strftime('%H:%M:%S')}Z`  {message.clean_content}"
                big_message += f"\n{await string.binify(self.bot.session, content)}"

            return [big_message[i : i + 2000] for i in range(0, len(big_message), 2000)]

        if (channel := self.get_claimed_channel(target)) :
            await channel.send(f"{target.mention}, you're still occupying this channel.")
            for message in await culminate(purged):
                await channel.send(message)

        elif (channel := await self.try_get_available_channel()) and (sc := self.get_support_channel(channel)):
            await sc.send_to_occupied(purged[0])
            await self.schedule(sc)
            await channel.send(
                f"You were redirected as the channel you attempted to open a support case in is already occupied."
            )
            for message in await culminate(purged):
                await channel.send(message)

        else:
            await self.redirect_channel.send(
                f"{target.name}, you were redirected as the channel you attempted to open a support case in is already occupied. Unfortunely, there are no available support channels, so you will need to wait for a channel to become available."
            )

    @commands.command(name="binify")
    async def binify_command(self, ctx: commands.Context, *, obj: t.Union[discord.Message, str]):
        async with ctx.typing():
            if isinstance(obj, discord.Message):
                if obj.attachments:
                    await obj.attachments[0].save(data := io.BytesIO())
                    file_contents = data.read().decode(encoding="utf-8")
                else:
                    file_contents = ""

                content = (
                    f"{await string.binify(self.bot.session, obj.clean_content, only_codeblocks=False)}" + "\n\n"
                    if obj.clean_content
                    else ""
                )
                file = f"{await string.binify(self.bot.session, file_contents) if file_contents else ''}"

                await ctx.send(f"**{string.possessive(obj.author)} message:**\n{content}{file}")
                await ctx.message.delete()
            else:
                await ctx.send(
                    f"{ctx.author.mention}:\n{await string.binify(self.bot.session, discord.utils.escape_mentions(obj), only_codeblocks=False)}"
                )
                await ctx.message.delete()

    # @commands.command(name="call")
    # @commands.cooldown(1, 21600, commands.BucketType.member)
    # async def call_command(self, ctx: commands.Context) -> None:
    #     # Calls a specified role. Useful for preventing mention spamming.
    #     pass


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Support(bot))
