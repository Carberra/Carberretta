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
import typing as t
from dataclasses import dataclass, field
from enum import Enum

import hikari
from lightbulb import commands, context, decorators, plugins

from carberretta import Config
from carberretta.utils import helpers

if t.TYPE_CHECKING:
    from lightbulb.app import BotApp

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

plugin = plugins.Plugin("Support")

log = logging.getLevelName(__name__)


class SupportState(Enum):
    UNAVAILABLE = 0
    OCCUPIED = 1
    AVAILABLE = 2


STATE_MAPPING: t.Final = {
    Config.UNAVAILABLE_SUPPORT_CATEGORY_ID: SupportState.UNAVAILABLE,
    Config.OCCUPIED_SUPPORT_CATEGORY_ID: SupportState.OCCUPIED,
    Config.AVAILABLE_SUPPORT_CATEGORY_ID: SupportState.AVAILABLE,
}


@dataclass(slots=True)
class SupportCase:
    client_id: int
    channel_id: int
    message_id: int
    case_id: str = field(default_factory=helpers.generate_id, kw_only=True)
    instance_id: str = field(default_factory=helpers.generate_id, kw_only=True)
    opened_at: dt.datetime = field(default_factory=dt.datetime.utcnow, kw_only=True)
    closed_at: dt.datetime | None = field(default=None, kw_only=True)

    @classmethod
    async def from_stored(
        cls, case_id: str, instance_id: str | None = None
    ) -> SupportCase:
        ...

    async def save(self) -> int:
        ...


class SupportChannel(hikari.GuildTextChannel):
    __slots__ = ("case",)

    def __init__(
        self, *args: t.Any, case: SupportCase | None = None, **kwargs: t.Any
    ) -> None:
        super().__init__(*args, **kwargs)
        self.case = case

    @classmethod
    async def from_channel(cls, channel: hikari.GuildTextChannel) -> SupportChannel:
        ...

    @property
    def state(self) -> SupportState:
        return (
            STATE_MAPPING.get(self.parent_id, SupportState.UNAVAILABLE)
            or SupportState.UNAVAILABLE
        )

    async def send_to(self, category: hikari.GuildCategory) -> None:
        ...


class SupportManager:
    ...


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_guild_message_create(event: hikari.GuildMessageCreateEvent) -> None:
    ...


@plugin.listener(hikari.MemberUpdateEvent)
async def on_member_update(event: hikari.MemberUpdateEvent) -> None:
    ...


@plugin.command
@decorators.command("client", "Check the client of a support case.")
@decorators.implements(commands.slash.SlashCommand)
async def cmd_client(ctx: context.base.Context) -> None:
    ...


@plugin.command
@decorators.command(
    "call",
    "Call for helpers. Carberretta will automatically work out whose help you need.",
)
@decorators.implements(commands.slash.SlashCommand)
async def cmd_call(ctx: context.base.Context) -> None:
    ...


@plugin.command
@decorators.option(
    "delay",
    "Close the case in this many minutes if there is no further activity.",
    type=int,
    default=0,
)
@decorators.command("close", "Close a support case.")
@decorators.implements(commands.slash.SlashCommand)
async def cmd_close(ctx: context.base.Context) -> None:
    ...


@plugin.command
@decorators.option(
    "member",
    "Re-open the last case this member opened.",
    type=hikari.Member,
    default=None,
)
@decorators.option(
    "case_id",
    "Re-open the case with this ID.",
    default=None,
)
@decorators.command(
    "reopen",
    "Re-open a support case. Re-opens the last case in this channel by default.",
)
@decorators.implements(commands.slash.SlashCommand)
async def cmd_reopen(ctx: context.base.Context) -> None:
    ...


@plugin.command
@decorators.option(
    "channel",
    "The channel to redirect the member to.",
    type=hikari.TextableGuildChannel,
    default=None,
)
@decorators.option(
    "member",
    "The member to redirect.",
    type=hikari.Member,
)
@decorators.command("redirect", "Redirect a member to another support channel.")
@decorators.implements(commands.slash.SlashCommand)
async def cmd_redirect(ctx: context.base.Context) -> None:
    ...


def load(bot: "BotApp") -> None:
    bot.add_plugin(plugin)


def unload(bot: "BotApp") -> None:
    bot.remove_plugin(plugin)
