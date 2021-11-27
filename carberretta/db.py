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
import logging
import os
import re
import typing as t
from pathlib import Path

import aiofiles
import aiosqlite

STRFTIME_PATTERN: t.Final = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}")

log = logging.getLogger(__name__)

ValueT = t.Union[int, float, dt.datetime, str, None]


class RowData(dict[str, t.Any]):
    def __repr__(self) -> str:
        return "RowData(" + ", ".join(f"{k}={v!r}" for k, v in self.items()) + ")"

    def __getattr__(self, key: str) -> t.Any:
        return self[key]

    def __setitem__(self, key: str, value: t.Any) -> None:
        raise ValueError("row data cannot be modified")

    def __setattr__(self, key: str, value: t.Any) -> None:
        raise ValueError("row data cannot be modified")

    def __delitem__(self, key: str) -> None:
        raise ValueError("row data cannot be modified")

    def __delattr__(self, key: str) -> None:
        raise ValueError("row data cannot be modified")

    @classmethod
    def from_selection(cls, cur: aiosqlite.Cursor, row: aiosqlite.Row) -> "RowData":
        def _resolve(field: int | float | str) -> t.Any:
            if isinstance(field, (int, float)) or not STRFTIME_PATTERN.match(field):
                return field

            return dt.datetime.strptime(field, "%Y-%m-%d %H:%M:%S")

        return cls((col[0], _resolve(row[i])) for i, col in enumerate(cur.description))


class Database:
    __slots__ = ("db_path", "sql_path", "calls", "cxn")

    def __init__(self, dynamic: "Path", static: "Path") -> None:
        self.db_path = (dynamic / "database.sqlite3").resolve()
        self.sql_path = (static / "build.sql").resolve()
        self.calls = 0

    async def connect(self) -> None:
        os.makedirs(self.db_path.parent, exist_ok=True)
        self.cxn = await aiosqlite.connect(self.db_path)
        log.info(f"Connected to database at {self.db_path}")

        self.cxn.row_factory = t.cast(t.Any, RowData.from_selection)
        await self.cxn.execute("pragma journal_mode=wal")
        await self.executescript(self.sql_path)
        log.info(f"Built database using {self.sql_path}")

        await self.cxn.commit()

    async def commit(self) -> None:
        await self.cxn.commit()

    async def close(self) -> None:
        await self.cxn.commit()
        await self.cxn.close()
        log.info("Closed database connection")

    async def try_fetch_field(self, command: str, *values: ValueT) -> ValueT:
        cur = await self.execute(command, *values)

        if (row := await cur.fetchone()) is None:
            return None

        return t.cast(ValueT, row[0])

    async def try_fetch_record(self, command: str, *values: ValueT) -> RowData | None:
        cur = await self.execute(command, *values)
        return t.cast(t.Optional[RowData], await cur.fetchone())

    async def fetch_records(self, command: str, *values: ValueT) -> t.Iterable[RowData]:
        cur = await self.execute(command, *values)
        return t.cast(t.Iterable[RowData], await cur.fetchall())

    async def fetch_column(
        self, command: str, *values: ValueT, index: int = 0
    ) -> list[ValueT]:
        cur = await self.execute(command, *values)

        if not (rows := await cur.fetchall()):
            return []

        return [row[index] for row in rows]

    async def execute(self, command: str, *values: ValueT) -> aiosqlite.Cursor:
        val_list = list(values)

        for i, v in enumerate(values):
            if isinstance(v, dt.datetime):
                val_list[i] = v.strftime("%Y-%m-%d %H:%M:%S")

        self.calls += 1
        cur = await self.cxn.execute(command, tuple(values))
        log.info(f"Executed query '{command}' ({cur.rowcount} rows modified)")
        return cur

    async def executemany(
        self, command: str, *values: tuple[ValueT, ...]
    ) -> aiosqlite.Cursor:
        self.calls += 1
        cur = await self.cxn.executemany(command, tuple(values))
        log.info(f"Executed multiquery '{command}' ({cur.rowcount} rows modified)")
        return cur

    async def executescript(self, path: Path | str) -> aiosqlite.Cursor:
        if not isinstance(path, Path):
            path = Path(path)
        path = path.resolve()

        async with aiofiles.open(path, encoding="utf-8") as f:
            cur = await self.cxn.executescript(await f.read())
            # fmt: off
            log.info(
                f"Executed script query from {path} ({cur.rowcount} rows modified)"
                .replace("-1", "unknown")
            )
            # fmt: on
            return cur
