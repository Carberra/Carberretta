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

import datetime as dt

from isodate import parse_duration


def aware_now() -> dt.datetime:
    return dt.datetime.now().astimezone()


def nat_delta(delta: dt.timedelta | int | float | str, ms: bool = False) -> str:
    if isinstance(delta, (int, float)):
        delta = dt.timedelta(seconds=delta)
    elif isinstance(delta, str):
        delta = parse_duration(delta)

    assert isinstance(delta, dt.timedelta)

    parts = []

    if delta.days != 0:
        parts.append(f"{delta.days:,}d")

    if (h := delta.seconds // 3600) != 0:
        parts.append(f"{h}h")

    if (m := delta.seconds // 60 - (60 * h)) != 0:
        parts.append(f"{m}m")

    if (s := delta.seconds - (60 * m) - (3600 * h)) != 0 or not parts:
        if ms:
            milli = round(delta.microseconds / 1000)
            parts.append(f"{s}.{milli:>03}s")
        else:
            parts.append(f"{s}s")

    return ", ".join(parts)
