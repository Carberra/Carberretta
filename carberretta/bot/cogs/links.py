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

    @commands.command(name="pep")
    async def command_pep(self, ctx: commands.Context, pep_number: int) -> None:
        async with self.bot.session.get(f"https://python.org/dev/peps/pep-{pep_number:04}") as response:
            if not 200 <= response.status <= 299:
                await ctx.send(f"PEP {pep_number:04} could not be found.")
                return

            await ctx.send(f"PEP {pep_number:04}: <https://python.org/dev/peps/pep-{pep_number:04}>")

    @commands.command(name="google", aliases=["lmgt", "lmgtfy"])
    async def command_google(self, ctx: commands.Context, *, query: str) -> None:
        if len(query) > 500:
            return await ctx.send("Your query should be no longer than 500 characters.")

        await ctx.send(f"<https://letmegooglethat.com/?q={query.replace(' ', '+')}>")
    
    @commands.command(name="duckduckgo", aliases=["ddg"])
    async def command_google(self, ctx: commands.Context, *, query: str) -> None:
        if len(query) > 500:
            return await ctx.send("Your query should be no longer than 500 characters.")

        await ctx.send(f"<https://duckduckgo.com/?q={query.replace(' ', '+')}>")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Links(bot))
