from aiosqlite import connect


class Database:
    def __init__(self, bot):
        self.bot = bot
        self.path = "./carberretta/data/dynamic/database.db3"
        self.build_path = "./carberretta/data/static/build.sql"

    async def connect(self):
        self.cxn = await connect(self.path)
        await self.cxn.execute("pragma journal_mode=wal")
        await self.executescript(self.build_path)
        await self.sync()
        await self.commit()

    async def commit(self):
        await self.cxn.commit()

    async def close(self):
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
