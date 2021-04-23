import discord
from discord.ext import commands


class Links(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @commands.command(name="youtube")
    async def command_youtube(self, ctx: commands.Context) -> None:
        await ctx.send("<https://youtube.carberra.xyz>")

    @commands.command(name="twitch")
    async def command_twitch(self, ctx: commands.Context) -> None:
        await ctx.send("<https://twitch.carberra.xyz>")

    @commands.command(name="lbry")
    async def command_lbry(self, ctx: commands.Context) -> None:
        await ctx.send("<https://lbry.carberra.xyz>")

    @commands.command(name="patreon")
    async def command_patreon(self, ctx: commands.Context) -> None:
        await ctx.send("<https://patreon.carberra.xyz>")

    @commands.command(name="twitter")
    async def command_twitter(self, ctx: commands.Context) -> None:
        await ctx.send("<https://twitter.carberra.xyz>")

    @commands.command(name="facebook")
    async def command_facebook(self, ctx: commands.Context) -> None:
        await ctx.send("<https://facebook.carberra.xyz>")

    @commands.command(name="github")
    async def command_github(self, ctx: commands.Context) -> None:
        await ctx.send("<https://github.carberra.xyz>")

    @commands.command(name="donate")
    async def command_donate(self, ctx: commands.Context) -> None:
        await ctx.send("<https://donate.carberra.xyz>")

    @commands.command(name="plans")
    async def command_plans(self, ctx: commands.Context) -> None:
        await ctx.send("<https://plans.carberra.xyz>")

    @commands.command(name="docs")
    async def command_docs(self, ctx: commands.Context) -> None:
        await ctx.send("<https://docs.carberra.xyz>")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Links(bot))
