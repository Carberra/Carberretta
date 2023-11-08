import datetime as dt

import discord
from discord.ext import commands

from carberretta import Config

TIMEOUT = 600


class Gateway(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.gateway_channel = self.bot.get_channel(Config.GATEWAY_ID)
            self.announcements_role = self.gateway_channel.guild.get_role(Config.ANNOUNCEMENTS_ROLE_ID)
            self.videos_role = self.gateway_channel.guild.get_role(Config.VIDEOS_ROLE_ID)
            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        if member.guild.id != Config.GUILD_ID:
            return

        if member.bot:
            await self.gateway_channel.send(f"A new bot, {member.mention}, has joined the server.")
            return

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        if member.guild.id != Config.GUILD_ID:
            return

        try:
            return self.bot.scheduler.get_job(f"{member.id}").remove()
        except AttributeError:
            if member.pending:
                return

            await self.gateway_channel.send(f"{member.display_name} is no longer in the server. (ID: {member.id})")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if after.guild.id != Config.GUILD_ID:
            return

        if before.pending != after.pending:
            await self.gateway_channel.send(
                f"Welcome to Carberra {after.mention}! Make yourself at home in "
                "<#626608699942764548>, and look at <#739572184745377813> to find out "
                "how to get support."
            )


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Gateway(bot))
