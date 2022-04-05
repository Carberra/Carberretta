# Hi carb

import re
import zlib
import io
from rapidfuzz import fuzz
from rapidfuzz import process

async def get_rtfm(value, cache):
    matches = process.extract(value, cache.keys(), scorer=fuzz.QRatio, limit=15)
    match = []
    for result, _, _ in matches:
        match.append(result)
    return match

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
        def decomepress(bytes_obj):
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
    for line in decompress_chunks(bytes_obj):
        if not (match := regex.match(line.rstrip())):
            continue
        if match in cache:
            continue
        direct, type, i, link, e = match.groups()
        cache[direct] = (match.groups(), link)
    return cache
