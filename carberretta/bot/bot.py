from asyncio import sleep
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord import Status
from discord.ext.commands import Bot as BotBase, Context

from carberretta import Config
from carberretta.db import Database
from carberretta.utils import Ready


class Bot(BotBase):
    def __init__(self, version):
        self.version = version
        self._cogs = [p.stem for p in Path(".").glob("./carberretta/bot/cogs/*.py")]
        self._dynamic = "./carberretta/data/dynamic"
        self._static = "./carberretta/data/static"

        self.ready = Ready(self)
        self.scheduler = AsyncIOScheduler()
        self.db = Database(self)

        super().__init__(command_prefix=Config.PREFIX, case_insensitive=True, owner_ids=Config.OWNER_IDS, status=Status.dnd)

    def setup(self):
        print("running setup...")

        for cog in self._cogs:
            self.load_extension(f"carberretta.bot.cogs.{cog}")
            print(f" {cog} cog loaded")

        print("setup complete")

    def run(self):
        self.setup()

        print(f"running bot...")
        super().run(Config.TOKEN, reconnect=True)

    async def close(self):
        print("closing on keyboard interrupt...")
        await self.shutdown()

    async def shutdown(self):
        print("shutting down...")
        self.scheduler.shutdown()
        await self.db.commit()
        await self.db.close()

        hub = self.get_cog("Hub")
        await hub.stdout.send(f"Carberretta is shutting down. (Version {self.version})")
        await super().close()

    async def process_comamnds(self, msg):
        ctx = await self.get_context(msg, cls=Context)

        if ctx.command is not None:
            if self.ready.bot:
                await self.invoke(ctx)

            else:
                await ctx.send(
                    "Carberretta is not ready to receive commands. Try again in a few seconds.", delete_after=5
                )

    # async def on_error(self, err, *args, **kwargs):
    # 	pass

    # async def on_command_error(self, ctx, exc):
    # 	pass

    async def on_connect(self):
        print(f" bot connected")

        if not self.ready.booted:
            await self.db.connect()
            print(" connected to and synced database")

    async def on_disconnect(self):
        print(" bot disconnected")

    async def on_ready(self):
        if not self.ready.booted:
            self.scheduler.start()
            print(f" scheduler started ({len(self.scheduler.get_jobs()):,} job(s) scheduled)")

            self.guild = self.get_guild(Config.GUILD_ID)

            # This ensures the cogs boot properly while allowing cogs to
            #  ready themselves in their own time
            await sleep(0.1)
            self.ready.booted = True
            print(" bot booted")

        else:
            print(f" bot reconnected (DWSP latency: {self.latency*1000:,.0f})")

        # presence = self.get_cog("Presence")
        # await presence.set()

    async def on_message(self, msg):
        if not msg.author.bot:
            await self.process_comamnds(msg)
