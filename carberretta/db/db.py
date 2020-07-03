from os.path import isdir

from aiosqlite import connect


class Database:
    def __init__(self, bot):
        self.bot = bot
        self.path = f"{self.bot._dynamic}/database.db3"
        self.build_path = f"{self.bot._static}/build.sql"

    async def connect(self):
        if not isdir(self.bot._dynamic):
            # If cloned, this dir likely won't exist, so make it.
            from os import makedirs
            makedirs(self.bot._dynamic)

        self.cxn = await connect(self.path)
        await self.execute("pragma journal_mode=wal")
        await self.executescript(self.build_path)
        await self.sync()
        await self.commit()

    async def commit(self):
        await self.cxn.commit()

    async def close(self):
        await self.commit()
        await self.cxn.close()

    async def sync(self):
        pass

    async def field(self, command, *values):
        cur = await self.cxn.execute(command, tuple(values))

        if (row := await cur.fetchone()) is not None:
            return row[0]

    async def record(self, command, *values):
        cur = await self.cxn.execute(command, tuple(values))

        return await cur.fetchone()

    async def records(self, command, *values):
        cur = await self.cxn.execute(command, tuple(values))

        return await cur.fetchall()

    async def column(self, command, *values):
        cur = await self.cxn.execute(command, tuple(values))

        return [row[0] for row in await cur.fetchall()]

    async def execute(self, command, *values):
        await self.cxn.execute(command, tuple(values))

    async def executemany(self, command, valueset):
        await self.cxn.executemany(command, valueset)

    async def executescript(self, path, **kwargs):
        with open(path, "r", encoding="utf-8") as script:
            await self.cxn.executescript(script.read().format(**kwargs))
