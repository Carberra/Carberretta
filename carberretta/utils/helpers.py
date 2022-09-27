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

import hashlib
import logging
import random
import time
import warnings
from io import StringIO


def choose_colour() -> int:
    return random.choice(  # nosec B311
        (
            0x1ABC9C,
            0x11806A,
            0x2ECC71,
            0x1F8B4C,
            0x3498DB,
            0x206694,
            0x9B59B6,
            0x71368A,
            0xE91E63,
            0xAD1457,
            0xF1C40F,
            0xC27C0E,
            0xE67E22,
            0xA84300,
            0xE74C3C,
            0x992D22,
            # 0x95a5a6,
            # 0x979c9f,
            # 0x607d8b,
            # 0x546e7a,
        )
    )


def generate_id() -> str:
    return hashlib.md5(f"{time.time()}".encode(), usedforsecurity=False).hexdigest()


def configure_logging(level: int = logging.INFO) -> StringIO:
    # Hikari doesn't allow for the adding of additional handlers, so
    # we'll just do it ourselves.

    FMT = "{asctime} [{levelname:^9}] {name}: {message}"
    COLOURS = {
        logging.DEBUG: "\33[38;5;244m",
        logging.INFO: "\33[38;5;248m",
        logging.WARNING: "\33[1m\33[38;5;178m",
        logging.ERROR: "\33[1m\33[38;5;196m",
        logging.CRITICAL: "\33[1m\33[48;5;196m",
    }

    class ConsoleFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            log_fmt = f"{COLOURS[record.levelno]}{FMT}\33[0m"
            formatter = logging.Formatter(log_fmt, style="{")
            return formatter.format(record)

    class StringIOFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            formatter = logging.Formatter(FMT, style="{")
            return formatter.format(record)

    console = logging.StreamHandler()
    console.setFormatter(ConsoleFormatter())

    string_io = logging.StreamHandler(stream=(stream := StringIO()))
    string_io.setFormatter(StringIOFormatter())

    logging.basicConfig(
        level=level,
        handlers=[console, string_io],
    )

    # Optimise and set extra options.
    logging.logThreads = False
    logging.logProcesses = False
    warnings.simplefilter("always", DeprecationWarning)
    logging.captureWarnings(True)

    # Return the stream to be accessed later.
    return stream
