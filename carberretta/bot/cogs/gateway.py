import datetime as dt

import discord
from discord.ext import commands

from carberretta import Config

TIMEOUT = 600


class Gateway(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def schedule_action(self, member: discord.Member, secs: int = TIMEOUT) -> None:
        async def _take_action(member: discord.Member) -> None:
            if member.pending:
                return await member.kick(
                    reason=(
                        "Member failed to accept the server rules before "
                        "being timed out."
                    )
                )

            await member.add_roles(
                self.announcements_role,
                self.videos_role,
                reason="Member accepted the server rules.",
                atomic=False
            )

        self.bot.scheduler.add_job(
            _take_action,
            id=f"{member.id}",
            next_run_time=dt.datetime.utcnow() + dt.timedelta(seconds=secs),
            args=[member],
        )

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.gateway_channel = self.bot.get_channel(Config.GATEWAY_ID)
            self.announcements_role = self.gateway_channel.guild.get_role(Config.ANNOUNCEMENTS_ROLE_ID)
            self.videos_role = self.gateway_channel.guild.get_role(Config.VIDEOS_ROLE_ID)

            for m in self.gateway_channel.guild.members:
                if (secs := (dt.datetime.utcnow() - m.joined_at).seconds) <= TIMEOUT:
                    await self.schedule_action(m, secs=TIMEOUT - secs)
                elif m.pending:
                    await m.kick(
                        reason=(
                            "Member failed to accept the server rules before "
                            "being timed out."
                        )
                    )

            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.guild.id != Config.GUILD_ID:
            return

        await self.schedule_action(member)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if member.guild.id != Config.GUILD_ID:
            return

        try:
            return self.bot.scheduler.get_job(f"{member.id}").remove()
        except AttributeError:
            if member.pending:
                return

            await self.gateway_channel.send(
                f"{member.display_name} is no longer in the server. "
                f"(ID: {member.id})"
            )

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if after.guild.id != Config.GUILD_ID:
            return

        if before.pending != after.pending:
            humans = len([m for m in after.guild.members if not m.bot])
            await self.gateway_channel.send(
                f"Welcome {after.mention}! You are member nº {humans:,} of "
                "Carberra Tutorials (excluding bots). Make yourself at home "
                "in <#626608699942764548>, and look at <#739572184745377813> "
                "to find out how to get support."
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Gateway(bot))
