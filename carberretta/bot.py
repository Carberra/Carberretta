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

import asyncio
import logging
import os
import traceback
from http.cookies import SimpleCookie
from pathlib import Path

import hikari
import lightbulb
from aiohttp import ClientSession, CookieJar
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from hikari.events.base_events import EventT
from pytz import utc

import carberretta
from carberretta import Config, Database
from carberretta.utils import helpers

log = logging.getLogger(__name__)

bot = lightbulb.BotApp(
    Config.TOKEN,
    default_enabled_guilds=Config.GUILD_ID,
    owner_ids=Config.OWNER_IDS,
    case_insensitive_prefix_commands=True,
    intents=hikari.Intents.ALL,
)
bot.d._dynamic = Path("./data/dynamic")
bot.d._static = bot.d._dynamic.parent / "static"

bot.d.scheduler = AsyncIOScheduler()
bot.d.scheduler.configure(timezone=utc)

bot.load_extensions_from("./carberretta/extensions")


@bot.listen(hikari.StartingEvent)
async def on_starting(_: hikari.StartingEvent) -> None:
    cookie_jar = CookieJar(loop=asyncio.get_running_loop())
    cookie_jar.update_cookies(SimpleCookie("CONSENT=YES+cb; Domain=.youtube.com"))
    log.info("YouTube cookies set")

    bot.d.scheduler.start()
    bot.d.session = ClientSession(trust_env=True, cookie_jar=cookie_jar)
    log.info("AIOHTTP session started")

    bot.d.db = Database(bot.d._dynamic, bot.d._static)
    await bot.d.db.connect()
    bot.d.scheduler.add_job(bot.d.db.commit, CronTrigger(second=0))


# @bot.listen(hikari.StartedEvent)
# async def on_started(_: hikari.StartedEvent) -> None:
#     ...


@bot.listen(hikari.StoppingEvent)
async def on_stopping(_: hikari.StoppingEvent) -> None:
    await bot.d.db.close()
    await bot.d.session.close()
    log.info("AIOHTTP session closed")
    bot.d.scheduler.shutdown()


@bot.listen(hikari.DMMessageCreateEvent)
async def on_dm_message_create(event: hikari.DMMessageCreateEvent) -> None:
    if event.message.author.is_bot:
        return

    await event.message.respond(
        f"You need to DM <@{795985066530439229}> to send a message to moderators."
    )


@bot.listen(hikari.ExceptionEvent)
async def on_error(event: hikari.ExceptionEvent[EventT]) -> None:
    raise event.exception


@bot.listen(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    exc = event.exception

    if isinstance(exc, lightbulb.NotOwner):
        await event.context.respond("You need to be an owner to do that.")
        return

    if isinstance(exc, lightbulb.MissingRequiredPermission):
        await event.context.respond(
            f"You are missing the following permissions: {exc.missing_perms}"
        )
        return

    try:
        err_id = helpers.generate_id()
        await bot.d.db.execute(
            "INSERT INTO errors (err_id, err_cmd, err_text) VALUES (?, ?, ?)",
            err_id,
            event.context.invoked_with,
            "".join(traceback.format_exception(event.exception)),
        )
        await event.context.respond(
            "Something went wrong. An error report has been created "
            f"(ID: {err_id[:7]})."
        )
    finally:
        raise event.exception


def run() -> None:
    if os.name != "nt":
        import uvloop

        uvloop.install()

    bot.run(
        activity=hikari.Activity(
            name=f"/help • Version {carberretta.__version__}",
            type=hikari.ActivityType.WATCHING,
        )
    )
