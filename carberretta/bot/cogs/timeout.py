import datetime as dt
import time
import typing as t

import discord
from discord.ext import commands

from carberretta import Config


class Timeout(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.moderator_role = self.bot.get_guild(Config.GUILD_ID).get_role(Config.MODERATOR_ROLE_ID)
            self.bot.ready.up(self)

    @commands.command(name="timeout", aliases=["mute"])
    async def timeout_command(
        self,
        ctx: commands.Context,
        target: t.Optional[discord.Member],
        seconds: int,
    ) -> None:
        # This is a hodge-podge command, and shouldn't *really* be taken seriously.
        if self.moderator_role not in ctx.author.roles:
            await ctx.send("You can't do that.")
            return

        if not 1 <= seconds <= 2_419_200:
            await ctx.send("The timeout must be between 1 second and 28 days inclusive.")
            return

        url = f"https://discord.com/api/v9/guilds/{Config.GUILD_ID}/members/{target.id}"
        headers = {
            "User-Agent": "Carberretta",
            "Authorization": f"Bot {Config.TOKEN}",
            "Content-Type": "application/json",
        }
        data = {
            "communication_disabled_until": (dt.datetime.utcnow() + dt.timedelta(seconds=seconds)).isoformat()
        }

        async with self.bot.session.patch(url, headers=headers, json=data) as r:
            if not 200 <= r.status <= 299:
                await ctx.send(f"Timeout failed (status: {r.status})")
                return

            await ctx.send("Done.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Timeout(bot))
