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

<<<<<<< HEAD
import re
import zlib
import io
from rapidfuzz import fuzz
from rapidfuzz import process

async def get_rtfm(value, cache):
=======
import io
import re
import zlib
from typing import Any, Generator

from rapidfuzz import fuzz, process


async def get_rtfm(value: str | Any, cache: dict[str, str]) -> list[str | Any]:
>>>>>>> b651126 (Updated pr for RTFM command)
    matches = process.extract(value, cache.keys(), scorer=fuzz.QRatio, limit=15)
    match = []
    for result, _, _ in matches:
        match.append(result)
    return match

<<<<<<< HEAD
def decode_object_inv(stream):
    cache = {}
    bytes_obj = io.BytesIO(stream)
    inv_version = bytes_obj.readline().decode("utf-8").rstrip() #This line is the inv version
    if inv_version != "# Sphinx inventory version 2":
        raise RuntimeError("Invalid object inv version")
    name = bytes_obj.readline().decode("utf-8").rstrip()[11:] #This line is the project's name
    version = bytes_obj.readline().decode("utf-8").rstrip()[11:] #This line is the project's version
    zlib_line = bytes_obj.readline().decode("utf-8")
    if "zlib" not in zlib_line: #The line that has Zlib in it
        raise RuntimeError("Invalid object.inv file")
    regex = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)") #this thing is scary af
    def decompress_chunks(bytes_obj):
        def decompress(bytes_obj):
            decompressor = zlib.decompressobj()
            for chunk in bytes_obj:
                chunk = decompressor.decompress(chunk) #decompresses to somethign
                yield chunk #yields chunks
            this = decompressor.flush()
            yield this #yields this flush thing which is normally b''
        cache = b""
        for chunk in decomepress(bytes_obj):
            cache += chunk
            pos = cache.find(b"\n")
            while pos != -1:
                yield cache[:pos].decode("utf-8") #decodes to normal text
                cache = cache[pos + 1:]
                pos = cache.find(b"\n")
=======

def decode_object_inv(
    stream: bytes,
) -> dict[str | Any, tuple[tuple[str | Any, ...], str | Any]]:
    cache = {}
    bytes_obj = io.BytesIO(stream)
    inv_version = (
        bytes_obj.readline().decode("utf-8").rstrip()
    )  # This line is the inv version
    if inv_version != "# Sphinx inventory version 2":
        raise RuntimeError("Invalid object inv version")
    name = (
        bytes_obj.readline().decode("utf-8").rstrip()[11:]
    )  # This line is the project's name
    version = (
        bytes_obj.readline().decode("utf-8").rstrip()[11:]
    )  # This line is the project's version
    zlib_line = bytes_obj.readline().decode("utf-8")
    if "zlib" not in zlib_line:  # The line that has Zlib in it
        raise RuntimeError("Invalid object.inv file")
    regex = re.compile(r"(?x)(.+?)\s+(\S*:\S*)\s+(-?\d+)\s+(\S+)\s+(.*)")  # scary

    def decompress_chunks(bytes_obj: io.BytesIO) -> Generator[str, None, None]:
        def decompress(bytes_obj: io.BytesIO) -> Generator[bytes | int, None, None]:
            decompressor = zlib.decompressobj()
            for chunk in bytes_obj:
                chunk = decompressor.decompress(chunk)  # decompresses to something
                yield chunk  # yields chunks
            flush = decompressor.flush()
            yield flush  # yields this flush thing which is normally b''

        cache = b""
        for chunk in decompress(bytes_obj):
            if isinstance(chunk, bytes):
                cache += chunk
            pos = cache.find(b"\n")
            while pos != -1:
                yield cache[:pos].decode("utf-8")  # decodes to normal text
                cache = cache[pos + 1 :]
                pos = cache.find(b"\n")

>>>>>>> b651126 (Updated pr for RTFM command)
    for line in decompress_chunks(bytes_obj):
        if not (match := regex.match(line.rstrip())):
            continue
        if match in cache:
            continue
<<<<<<< HEAD
        direct, type, i, link, e = match.groups()
=======
        direct, _, _, link, _ = match.groups()
>>>>>>> b651126 (Updated pr for RTFM command)
        cache[direct] = (match.groups(), link)
    return cache
