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

from __future__ import annotations

import datetime as dt
import re
import typing as t

from aiohttp import ClientSession

if t.TYPE_CHECKING:
    from hikari import User

ORDINAL_ENDINGS: t.Final = {"1": "st", "2": "nd", "3": "rd"}


def list_of(items: list[str], sep: str = "and") -> str:
    if len(items) > 2:
        return f"{', '.join(items[:-1])}, {sep} {items[-1]}"

    return f" {sep} ".join(items)


def ordinal(number: int) -> str:
    if str(number)[-2:] not in ("11", "12", "13"):
        return f"{number:,}{ORDINAL_ENDINGS.get(str(number)[-1], 'th')}"

    return f"{number:,}th"


def possessive(user: User) -> str:
    name = getattr(user, "display_name", user.username)
    return f"{name}'{'s' if not name.endswith('s') else ''}"


async def binify(
    session: ClientSession,
    text: str,
    filename: str,
    *,
    only_codeblocks: bool = False,
    expires_in_days: int = 7,
    file_extension: str = "",
) -> str:
    async def convert(body: str, to_replace: str, ext: str) -> str:
        payload = {
            "files": [{"filename": f"{filename}{ext}", "content": body}],
            "expires": str(dt.datetime.now() + dt.timedelta(expires_in_days)),
        }

        async with session.put("https://api.mystb.in/paste", json=payload) as resp:
            if not resp.ok:
                return f"Failed calling Mystbin. HTTP status code: {resp.status}"

            data = await resp.json()
            return text.replace(to_replace, f"<https://mystb.in/{data['id']}>")

    if not only_codeblocks:
        return await convert(text, text, file_extension)

    while (match := re.search(r"```([a-z]*)(\n?)([\s\S]*?)\n?```", text)) is not None:
        if not match.group(2):
            code = match.group(1) + match.group(3)
        else:
            code = match.group(3) or match.group(1) or "None"
            if match.group(1):
                file_extension = f".{match.group(1)}"

        text = await convert(code, match.group(0), file_extension)

    return text
