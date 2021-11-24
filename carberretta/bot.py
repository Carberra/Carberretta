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

import logging
import os
from pathlib import Path

import hikari
from aiohttp import ClientSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from lightbulb.app import BotApp
from pytz import utc

import carberretta
from carberretta import Config

log = logging.getLogger(__name__)

bot = BotApp(
    Config.TOKEN,
    prefix=Config.PREFIX,
    default_enabled_guilds=[Config.GUILD_ID, Config.HUB_GUILD_ID],
    owner_ids=Config.OWNER_IDS,
    case_insensitive_prefix_commands=True,
    intents=hikari.Intents.ALL,
)
bot.d._dynamic = Path("./carberretta/data/dynamic")
bot.d._static = bot.d._dynamic.parent / "static"

bot.d.scheduler = AsyncIOScheduler()
bot.d.scheduler.configure(timezone=utc)

bot.load_extensions_from("./carberretta/extensions")


@bot.listen(hikari.StartingEvent)
async def on_starting(event: hikari.StartingEvent) -> None:
    bot.d.scheduler.start()
    bot.d.session = ClientSession(trust_env=True)
    log.info("AIOHTTP session started")


@bot.listen(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent) -> None:
    await bot.rest.create_message(
        Config.HUB_STDOUT_CHANNEL_ID,
        f"Carberretta is now online! (Version {carberretta.__version__})",
    )


@bot.listen(hikari.StoppingEvent)
async def on_stopping(event: hikari.StoppingEvent) -> None:
    bot.d.scheduler.shutdown()
    await bot.d.session.close()
    log.info("AIOHTTP session closed")

    await bot.rest.create_message(
        Config.HUB_STDOUT_CHANNEL_ID,
        f"Carberretta is shutting down. (Version {carberretta.__version__})",
    )


def run() -> None:
    if os.name != "nt":
        import uvloop

        uvloop.install()

    bot.run()
