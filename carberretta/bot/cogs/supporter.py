import discord
from discord.ext import commands

from carberretta import Config


class Supporter(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.supporter_role = self.bot.guild.get_role(Config.SUPPORTER_ROLE_ID)
            self.patron_role = self.bot.guild.get_role(Config.PATRON_ROLE_ID)
            self.sub_role = self.bot.guild.get_role(Config.TWITCH_SUB_ROLE_ID)
            self.booster_role = self.bot.guild.get_role(Config.BOOSTER_ROLE_ID)

            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if self.bot.ready.supporter:
            added = set(after.roles) - set(before.roles)
            if any(r in added for r in (self.patron_role, self.sub_role, self.booster_role)):
                await after.add_roles(self.supporter_role, reason="Received supporting role.")

            removed = set(before.roles) - set(after.roles)
            if any(r in removed for r in (self.patron_role, self.sub_role, self.booster_role)):
                await after.remove_roles(self.supporter_role, reason="Lost supporting role.")

    @commands.command(name="syncroles")
    @commands.is_owner()
    async def command_syncroles(self, ctx: commands.Context) -> None:
        with ctx.typing():
            for member in self.bot.guild.members:
                if self.supporter_role in member.roles:
                    if not any(r in member.roles for r in (self.patron_role, self.sub_role, self.booster_role)):
                        await member.remove_roles(self.supporter_role, reason="Lost supporting role(s).")

                else:
                    if any(r in member.roles for r in (self.patron_role, self.sub_role, self.booster_role)):
                        await member.add_roles(self.supporter_role, reason="Received supporting role(s).")

            await ctx.send("Done.")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Supporter(bot))
