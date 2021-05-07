import asyncio
import datetime as dt
import traceback
from pathlib import Path
from pytz import utc

import aiohttp
import discord
from aiohttp import ClientSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands

from carberretta import Config, utils
from carberretta.db import Database


class Bot(commands.Bot):
    def __init__(self, version):
        self.version = version
        self._cogs = [p.stem for p in Path(".").glob("./carberretta/bot/cogs/*.py")]
        self._dynamic = "./carberretta/data/dynamic"
        self._static = "./carberretta/data/static"

        self.scheduler = AsyncIOScheduler()
        self.session = ClientSession()
        self.db = Database(self)
        self.emoji = utils.EmojiGetter(self)
        self.loc = utils.CodeCounter()
        self.ready = utils.Ready(self)

        self.scheduler.configure(timezone=utc)
        self.loc.count()

        super().__init__(
            command_prefix=self.command_prefix,
            case_insensitive=True,
            owner_ids=Config.OWNER_IDS,
            status=discord.Status.dnd,
            intents=discord.Intents.all(),
        )

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
        print("shutting down...")
        for cog in self.cogs.values():
            if hasattr(cog, "on_shutdown"):
                await cog.on_shutdown()

        self.scheduler.shutdown()
        await self.db.close()
        await self.session.close()

        hub = self.get_cog("Hub")
        await hub.stdout.send(f"Carberretta is shutting down. (Version {self.version})")
        await super().close()

    async def command_prefix(self, bot, message):
        return commands.when_mentioned_or(Config.PREFIX)(bot, message)

    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=commands.Context)

        if ctx.command is None:
            return

        if not self.ready.bot:
            return await ctx.send(
                "Carberretta is not ready to receive commands. Try again in a few seconds.", delete_after=5
            )

        support = self.get_cog("Support")
        if ctx.channel in [sc.channel for sc in support.available_channels] and ctx.command.name != "reopen":
            return await ctx.message.delete()

        await self.invoke(ctx)

    async def on_error(self, err, *args, **kwargs):
        async with self.session.post("https://mystb.in/documents", data=traceback.format_exc()) as response:
            if 200 <= response.status <= 299:
                data = await response.json()
                link = f"https://mystb.in/{data['key']}"
            else:
                link = f"[No link: {response.status} status]"

        hub = self.get_cog("Hub")
        await hub.stdout.send(f"Something went wrong: <{link}>")

        if err == "on_command_error":
            await args[0].send("Something went wrong. Let Carberra or Max know.")

        raise  # Re-raises the last known exception.

    async def on_command_error(self, ctx, exc):
        if isinstance(exc, commands.CommandNotFound):
            pass

        # Custom check failure handling.
        elif hasattr(exc, "msg"):
            await ctx.send(exc.msg)

        elif isinstance(exc, commands.MissingRequiredArgument):
            await ctx.send(f"No `{exc.param.name}` argument was passed, despite being required.")

        elif isinstance(exc, commands.BadArgument):
            await ctx.send(f"One or more arguments are invalid.")

        elif isinstance(exc, commands.TooManyArguments):
            await ctx.send(f"Too many arguments have been passed.",)

        elif isinstance(exc, commands.MissingPermissions):
            mp = utils.string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms], sep="or")
            await ctx.send(f"You do not have the {mp} permission(s), which are required to use this command.")

        elif isinstance(exc, commands.BotMissingPermissions):
            try:
                mp = utils.string.list_of(
                    [str(perm.replace("_", " ")).title() for perm in exc.missing_perms], sep="or"
                )
                await ctx.send(
                    f"Carberretta does not have the {mp} permission(s), which are required to use this command."
                )
            except discord.Forbidden:
                # If Carberretta does not have the Send Messages permission
                # (might redirect this to log channel once it's set up).
                pass

        elif isinstance(exc, commands.NotOwner):
            await ctx.send(f"That command can only be used by Carberretta's owner.")

        elif isinstance(exc, commands.CommandOnCooldown):
            # Hooray for discord.py str() logic.
            cooldown_texts = {
                "BucketType.user": "You can not use the `{}` command for another {}.",
                "BucketType.guild": "The `{}` command can not be used in this server for another {}.",
                "BucketType.channel": "The `{}` command can not be used in this channel for another {}.",
                "BucketType.member": "You can not use the `{}` command in this server for another {}.",
                "BucketType.category": "The `{}` command can not be used in this category for another {}.",
            }
            await ctx.message.delete()
            await ctx.send(
                cooldown_texts[str(exc.cooldown.type)].format(
                    ctx.command.name, utils.chron.long_delta(dt.timedelta(seconds=exc.retry_after))
                ),
                delete_after=10,
            )

        elif isinstance(exc, commands.InvalidEndOfQuotedStringError):
            await ctx.send(
                f"Carberretta expected a space after the closing quote, but found a(n) `{exc.char}` instead."
            )

        elif isinstance(exc, commands.ExpectedClosingQuoteError):
            await ctx.send(f"Carberretta expected a closing quote character, but did not find one.")

        # Base errors.
        elif isinstance(exc, commands.UserInputError):
            await ctx.send(f"There was an unhandled user input problem (probably argument passing error).")

        elif isinstance(exc, commands.CheckFailure):
            await ctx.send(f"There was an unhandled command check error (probably missing privileges).")

        # Non-command errors.
        elif (original := getattr(exc, "original", None)) is not None:
            if isinstance(original, discord.HTTPException):
                await ctx.send(f"A HTTP exception occurred ({original.status})\n```{original.text}```")
            else:
                raise original

        else:
            raise exc

    async def on_connect(self):
        print(f" bot connected")

        if not self.ready.booted:
            await self.db.connect()
            print(" connected to and built database")

    async def on_disconnect(self):
        print(" bot disconnected")

    async def on_ready(self):
        if not self.ready.booted:
            self.scheduler.start()
            print(f" scheduler started ({len(self.scheduler.get_jobs()):,} job(s) scheduled)")

            self.guild = self.get_guild(Config.GUILD_ID)
            await self.db.sync()
            print(" synced database")

            self.ready.booted = True
            print(" bot booted")

        else:
            print(f" bot reconnected (DWSP latency: {self.latency*1000:,.0f})")

        presence = self.get_cog("Presence")
        await presence.set()

    async def on_message(self, message):
        if not message.author.bot and not isinstance(message.channel, discord.DMChannel):
            await self.process_commands(message)
