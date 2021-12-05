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
import logging
from io import BytesIO

import hikari
import lightbulb
from PIL import Image, ImageDraw, ImageFont

from carberretta import Config

RAVEPARTY_FONT = ImageFont.truetype("./data/static/raveparty_wide.ttf", 40)
FIRASANS_FONT = ImageFont.truetype("./data/static/firasans_regular.ttf", 100)

CARD_WIDTH = 1000
CARD_HEIGHT = 300

TIMEOUT = 600

plugin = lightbulb.Plugin("Gateway")

log = logging.getLogger(__name__)


async def schedule_action(member: hikari.Member, secs: int = TIMEOUT) -> None:
    async def _take_action(member_id: int) -> None:
        if not (member := plugin.bot.cache.get_member(Config.GUILD_ID, member_id)):
            return

        if member.is_pending:
            log.info(
                f"Member '{member.display_name}' kicked for not accepting "
                "the guidelines"
            )
            return await member.kick(
                reason="Member failed to accept the guidelines before being timed out."
            )

        log.info(
            f"Member '{member.display_name}' given roles for accepting the guidelines"
        )
        for role in [Config.ANNOUNCEMENTS_ROLE_ID, Config.VIDEOS_ROLE_ID]:
            await plugin.bot.rest.add_role_to_member(
                Config.GUILD_ID,
                member,
                role,
                reason="Member accepted the guidelines.",
            )

    plugin.bot.d.scheduler.add_job(
        _take_action,
        id=f"{member.id}",
        next_run_time=dt.datetime.utcnow() + dt.timedelta(seconds=secs),
        args=[member.id],
    )


@plugin.listener(hikari.StartedEvent)
async def on_started(_: hikari.StartedEvent) -> None:
    now = dt.datetime.now().astimezone()

    async for m in plugin.bot.rest.fetch_members(Config.GUILD_ID):
        if (secs := (now - m.joined_at).seconds) <= TIMEOUT:
            log.info(
                f"Member '{m.display_name}' joined while offline, scheduling action "
                f"in {TIMEOUT-secs} seconds..."
            )
            await schedule_action(m, secs=TIMEOUT - secs)

        elif m.is_pending:
            log.info(
                f"Member '{m.display_name}' kicked for not accepting the guidelines "
                "(on boot)"
            )
            await m.kick(
                reason="Member failed to accept the guidelines before being timed out."
            )


@plugin.listener(hikari.MemberCreateEvent)
async def on_member_join(event: hikari.MemberCreateEvent) -> None:
    if event.member.guild_id != Config.GUILD_ID:
        return

    log.info(f"Member '{event.member.display_name}' joined")
    await schedule_action(event.member)


@plugin.listener(hikari.MemberDeleteEvent)
async def on_member_leave(event: hikari.MemberDeleteEvent) -> None:
    member = event.old_member

    if not member:
        return

    if member.guild_id != Config.GUILD_ID:
        return

    try:
        plugin.bot.d.scheduler.get_job(f"{member.id}").remove()
        return
    except AttributeError:
        if member.is_pending:
            log.info(f"Member '{member.display_name}' left (was pending)")
            return

        log.info(f"Member '{member.display_name}' left")
        await plugin.bot.rest.create_message(
            Config.GATEWAY_CHANNEL_ID,
            f"{member.display_name} is no longer in the server. (ID: {member.id})",
        )


@plugin.listener(hikari.MemberUpdateEvent)
async def on_member_update(event: hikari.MemberUpdateEvent) -> None:
    if event.member.guild_id != Config.GUILD_ID:
        return

    if not event.old_member or not event.member:
        return

    if event.old_member.is_pending != event.member.is_pending:
        log.info(
            f"Member '{event.member.display_name}' accepted rules. "
            "Waiting to give roles..."
        )
        await send_welcome_message(event.member)


async def send_welcome_message(member: hikari.Member) -> None:
    back = Image.new("RGBA", (CARD_WIDTH * 4, CARD_HEIGHT * 4), (12, 12, 12, 255))

    async with plugin.bot.d.session.get(
        str(member.avatar_url or member.default_avatar_url)
    ) as resp:
        pfp = Image.open(BytesIO(await resp.read())).resize((250 * 4, 250 * 4))

    mask = Image.open("./data/static/circle_mask.jpg")

    back.paste(pfp, (50 * 4, 25 * 4), mask=mask)

    draw = ImageDraw.Draw(back)

    draw.ellipse((200 * 4, 175 * 4, 300 * 4, 275 * 4), fill=(12, 12, 12, 255))

    server_icon = Image.open("./data/static/server_icon.png").resize((80 * 4, 80 * 4))

    back.paste(server_icon, (210 * 4, 185 * 4), mask=mask.resize((80 * 4, 80 * 4)))

    radius = 25 * 4
    mask = Image.new("L", (radius * 2, radius * 2), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)

    alpha = Image.new("L", back.size, 255)
    w, h = back.size

    alpha.paste(mask.crop((0, 0, radius, radius)), box=(0, 0))
    alpha.paste(mask.crop((0, radius, radius, radius * 2)), box=(0, h - radius))
    alpha.paste(mask.crop((radius, 0, radius * 2, radius)), box=(w - radius, 0))
    alpha.paste(
        mask.crop((radius, radius, radius * 2, radius * 2)),
        box=(w - radius, h - radius),
    )

    back.putalpha(alpha)
    back = back.resize((CARD_WIDTH, CARD_HEIGHT))

    draw = ImageDraw.Draw(back)

    draw.text((325, 85), "welcome", fill="white", font=RAVEPARTY_FONT, anchor="lb")

    text = member.display_name

    w = draw.textsize(text, font=FIRASANS_FONT)[0]
    if w > 600:
        i = -1
        while w > 600:
            text = text[:i] + "..."
            i -= 1
            w = draw.textsize(text, font=FIRASANS_FONT)[0]
    draw.text(
        (318, 150),
        text=text,
        fill="white",
        font=FIRASANS_FONT,
        # align="right",
        anchor="lm",
    )

    humans = len(
        [
            m
            async for m in plugin.bot.rest.fetch_members(Config.GUILD_ID)
            if not m.is_bot
        ]
    )

    draw.text(
        (325, 250),
        f"member #{humans:,}",
        fill="white",
        font=RAVEPARTY_FONT,
        anchor="lb",
    )

    b = BytesIO()
    back.save(b, "PNG")
    b.seek(0)

    await plugin.bot.rest.create_message(
        Config.GATEWAY_CHANNEL_ID,
        f"Welcome {member.mention}! You are member nº {humans:,} of "
        "Carberra Tutorials (excluding bots). Make yourself at home "
        "in <#626608699942764548>, and look at <#739572184745377813> "
        "to find out how to get support.",
        attachment=hikari.Bytes(b, "welcome.png"),
        user_mentions=True,
    )


def load(bot: lightbulb.BotApp) -> None:
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
