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

import io
import re
import typing as t
import zlib

from rapidfuzz import fuzz, process

if t.TYPE_CHECKING:
    CachedObjT = dict[str | t.Any, tuple[tuple[str | t.Any, ...], str | t.Any]]


async def get_rtfm(value: str, cache: dict[str, str]) -> list[str]:
    matches = process.extract(value, cache.keys(), scorer=fuzz.QRatio, limit=15)
    return [result for result, _, _ in matches]


def decode_object_inv(
    stream: bytes,
) -> CachedObjT:
    cache: CachedObjT = {}
    bytes_obj = io.BytesIO(stream)

    if bytes_obj.readline().decode("utf-8").rstrip() != "# Sphinx inventory version 2":
        raise RuntimeError("Invalid object inv version")

    # Skip over the projects name and version
    bytes_obj.readline()
    bytes_obj.readline()

    if "zlib" not in bytes_obj.readline().decode("utf-8"):
        raise RuntimeError("Invalid object.inv file")

    regex = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")

    def decompress_chunks(bytes_obj: io.BytesIO) -> t.Generator[str, None, None]:
        def decompress(bytes_obj: io.BytesIO) -> t.Generator[bytes, None, None]:
            decompressor = zlib.decompressobj()

            for chunk in bytes_obj:
                yield decompressor.decompress(chunk)

            yield decompressor.flush()

        cache = b""
        for chunk in decompress(bytes_obj):
            cache += chunk
            pos = cache.find(b"\n")

            while pos != -1:
                yield cache[:pos].decode("utf-8")
                cache = cache[pos + 1 :]
                pos = cache.find(b"\n")

    for line in decompress_chunks(bytes_obj):
        if not (match := regex.match(line.rstrip())):
            continue

        if match in cache:
            continue

        direct, _, _, link, _ = match.groups()
        cache[direct] = (match.groups(), link)

    return cache
