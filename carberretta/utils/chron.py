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

import datetime as dt
import time

from carberretta.utils import string


def sys_time():
    return time.strftime("%H:%M:%S")


def utc_time():
    return dt.datetime.utcnow().strftime("%H:%M:%S")


def short_date(dt):
    return dt.strftime("%d/%m/%y")


def short_date_and_time(dt):
    return dt.strftime("%d/%m/%y %H:%M:%S")


def long_date(dt):
    return dt.strftime("%d %b %Y")


def long_date_and_time(dt):
    return dt.strftime("%d %b %Y at %H:%M:%S")


def short_delta(td, milliseconds=False):
    parts = []

    if td.days != 0:
        parts.append(f"{td.days:,}d")

    if (h := td.seconds // 3600) != 0:
        parts.append(f"{h}h")

    if (m := td.seconds // 60 - (60 * h)) != 0:
        parts.append(f"{m}m")

    if (s := td.seconds - (60 * m) - (3600 * h)) != 0 or not parts:
        if milliseconds:
            ms = round(td.microseconds / 1000)
            parts.append(f"{s}.{ms}s")
        else:
            parts.append(f"{s}s")

    return ", ".join(parts)


def long_delta(td, milliseconds=False):
    parts = []

    if (d := td.days) != 0:
        parts.append(f"{d:,} day{'s' if d > 1 else ''}")

    if (h := td.seconds // 3600) != 0:
        parts.append(f"{h} hour{'s' if h > 1 else ''}")

    if (m := td.seconds // 60 - (60 * h)) != 0:
        parts.append(f"{m} minute{'s' if m > 1 else ''}")

    if (s := td.seconds - (60 * m) - (3600 * h)) != 0 or not parts:
        if milliseconds:
            ms = round(td.microseconds / 1000)
            parts.append(f"{s}.{ms} seconds")
        else:
            parts.append(f"{s} second{'s' if s > 1 else ''}")

    return string.list_of(parts)


def from_iso(stamp):
    try:
        return dt.datetime.fromisoformat(stamp)
    except TypeError:
        # In case there's no records:
        return dt.datetime.min


def to_iso(obj):
    return obj.isoformat(" ")
