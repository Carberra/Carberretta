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

import typing as t
from dataclasses import dataclass
from json import dumps as json_dumps
from pathlib import Path

import aiofiles
import lightbulb
from content_filter import Filter

from carberretta.utils import chron

plugin = lightbulb.Plugin("Profanity")

FILTER_CONVERSION: t.Final[dict[str, str | None]] = {
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


@dataclass
class Profanity:
    file: str = ""
    filter: Filter = Filter(list_file=file)

    async def setup(self) -> None:
        if not Path(self.file).is_file():
            file_template: dict[str, list[t.Any] | None] = {
                "mainFilter": [],
                "dontFilter": None,
                "conditionFilter": [],
            }

            async with aiofiles.open(self.file, "w", encoding="utf-8") as f:
                await f.write(
                    json_dumps(file_template, cls=chron.DateTimeEncoder)
                )


async def into_filter_format(text: str) -> str:
    table: dict[int, str | None] = str.maketrans(FILTER_CONVERSION)
    return text.translate(table)


async def from_filter_format(text: str) -> str:
    return text.replace("#", "*")


def load(bot: lightbulb.BotApp) -> None:
    if not bot.d.profanity:
        bot.d.profanity = Profanity(file=f"{bot.d._dynamic}/filter.json")

    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    bot.remove_plugin(plugin)
