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
import json
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

import aiofiles
import hikari
import lightbulb
from content_filter import Filter

from carberretta.config import Config
from carberretta.utils import chron, helpers

plugin = lightbulb.Plugin("Profanity", include_datastore=True)


# ==== CONSTANTS ====


FILTER_CONVERSION: t.Final[t.Dict[str, str | None]] = {
    '"': None,
    ",": None,
    ".": None,
    "-": None,
    "'": None,
    "+": "t",
    "!": "i",
    "@": "a",
    "1": "i",
    "0": "o",
    "3": "e",
    "$": "s",
    "*": "#",
}

# actions should be in order of greatest to least in term of weight
AUTOMOD_ACTIONS: t.Final = ("ban", "kick", "warn", "verbal")

# ==== SETUP ====


@plugin.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent) -> None:
    await plugin.bot.d.profanity.setup()

    plugin.d.log_channel = await plugin.bot.rest.fetch_channel(Config.MODLOG_CHANNEL_ID)


# ==== MANAGE FILTER ====


@dataclass
class Profanity:
    file: str
    filter: Filter = field(default_factory=Filter)
    data: t.Dict[str, t.List[t.Dict[str, str | int | bool | None]] | t.Any] = field(
        default_factory=dict
    )

    async def setup(self) -> None:
        if not Path(self.file).is_file():
            self.data = {
                "mainFilter": [],
                "dontFilter": None,
                "conditionFilter": [],
            }

            async with aiofiles.open(self.file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(self.data, cls=chron.DateTimeEncoder))

        async with aiofiles.open(self.file, "r", encoding="utf-8") as f:
            self.data = json.loads(await f.read())

        self.filter = Filter(list_file=self.file)

    async def process(self, msg: str) -> t.List[bool | str | t.Dict[str, t.List[str]]]:
        res_raw: t.List[t.Dict[str, t.Any]] = self.filter.check(msg).as_list
        res: t.Dict[str, t.List[str]] = {"raw": [], "found": [], "count": []}
        actions: t.List[str] = []
        action: str = ""

        if not res_raw:
            return [False]

        for word in res_raw:
            res["raw"].append(word["find"] + "\n")
            res["found"].append(word["word"] + "\n")
            res["count"].append(str(word["count"]) + "\n")

            for w in self.data[word["filter"]]:
                if w["find"] == word["find"]:
                    actions.append(str(w["action"]))

        for a in AUTOMOD_ACTIONS:
            if a in actions:
                action = a

        return [True, res, action]


# ==== CUSTOM CONVERSIONS ====


async def into_filter_format(text: str) -> str:
    table: t.Dict[int, str | None] = str.maketrans(FILTER_CONVERSION)
    return text.translate(table)


async def from_filter_format(text: str) -> str:
    return text.replace("#", "*")


# ==== LISTENERS ====


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_guild_message_create(event: hikari.GuildMessageCreateEvent) -> None:
    if event.message.author.is_bot:
        return

    if event.message.channel_id == Config.MODERATOR_CHANNEL_ID:
        return

    if not (guild := event.get_guild()):
        return

    if not (member := guild.get_member(event.author.id)):
        return

    if not (channel := event.get_channel()):
        return

    res = await plugin.bot.d.profanity.process(event.message.content)

    if not res[0]:
        return

    await event.message.delete()
    msg = await channel.send(f"{member.mention}, please do not use offensive language.")

    await plugin.d.log_channel.send(
        hikari.Embed(
            title="Filtered Message",
            colour=helpers.choose_colour(),
            timestamp=dt.datetime.now().astimezone(),
        )
        .set_author(name="Modlog")
        .set_footer(f"{member.display_name}", icon=member.avatar_url)
        .add_field("Message", f"{event.message.content}")
        .add_field("Identified", f"{''.join(res[1]['raw'])}", inline=True)
        .add_field("Found", f"{''.join(res[1]['found'])}", inline=True)
        .add_field("Count", f"{''.join(res[1]['count'])}", inline=True)
        .add_field("Context", f"[Jump]({msg.make_link(guild)})", inline=True)
        .add_field("Action", f"{res[2].capitalize()}", inline=True)
    )


# ==== LOADING ====


def load(bot: lightbulb.BotApp) -> None:
    if not bot.d.profanity:
        bot.d.profanity = Profanity(file=f"{bot.d._dynamic}/filter.json")

    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
