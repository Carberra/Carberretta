"""
MISCELLANEOUS

A place for commands which don't fit anywhere else.
"""

import datetime
import unicodedata

import discord
from discord.ext import commands
from discord.ext.menus import MenuPages, ListPageSource

from carberretta.utils import DEFAULT_EMBED_COLOUR


class Leaderboard(ListPageSource):
    def __init__(self, ctx: commands.Context, data):
        self.ctx = ctx
        super().__init__(data, per_page=10)

    async def format_page(self, menu, entries):
        offset = (menu.current_page * self.per_page) + 1
        fields = []
        table = ("\n".join(
            f"{idx + offset}. **{entry[1]}** - {self.ctx.guild.get_member(entry[0])}"
            for idx, entry in enumerate(entries)))

        fields.append(("Hugs Given", table))
        
        len_data = len(self.entries)

        embed = discord.Embed(title="Hug Leaderboard", colour=self.ctx.author.colour)
        embed.set_thumbnail(url=self.ctx.guild.icon_url)
        embed.set_footer(text=f"{offset:,} - {min(len_data, offset + self.per_page + 1):,} of {len_data:,} members.")

        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)

        return embed


class Miscellaneous(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="hug", aliases=["huggies", "hugs", "huggie"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def hug_user_command(self, ctx: commands.Context, user: discord.Member):
        user_id = user.id
        user_id_2 = ctx.author.id
        times_hugged_others_2 = await self.bot.db.record("SELECT given FROM hugs WHERE UserID = ?",
                                                      user_id) or None
        times_hugged_others = await self.bot.db.record("SELECT given FROM hugs WHERE UserID = ?",
                                                     user_id_2) or None

        if user_id == user_id_2:
            await ctx.send("Congratulations, You Played Yourself")
            return

        if times_hugged_others_2 is None:
            await self.bot.db.execute('INSERT INTO hugs (UserID) VALUES (?)', user_id)
        if times_hugged_others is None:
            await self.bot.db.execute('INSERT INTO hugs (UserID) VALUES (?)', user_id_2)

        await self.bot.db.execute(
            'UPDATE hugLeaderboard SET given = given + 1 WHERE UserID = ?', user_id_2)
        await self.bot.db.execute('UPDATE hugLeaderboard SET received = received + 1 WHERE UserID = ?', user_id)
        received_count = await self.bot.db.record('SELECT received FROM hugs WHERE UserID = ?', user_id)
        await self.bot.db.commit()

        hug_file = discord.File('carberretta/data/static/hug.gif', filename='hug.gif')
        hug_embed = discord.Embed(title='Huggies', timestamp=datetime.datetime.utcnow(),
                                 description=f'You Hugged {user.display_name}')
        hug_embed.set_thumbnail(url='attachment://hug.gif')
        hug_embed.set_footer(text=f'now they have {received_count[0]} hug(s)', icon_url=user.avatar_url)
        await ctx.send(file=hug_file, embed=hug_embed)
        return

    @commands.command(name="huglb", aliases=["hugleaderboard"])
    async def hug_leaderboard_command(self, ctx: commands.Context):
        records = await self.bot.db.records(
            "SELECT UserID, given, received FROM hugs ORDER BY given DESC")
        menu = MenuPages(source=Leaderboard(ctx, records),
                         clear_reactions_after=True,
                         timeout=60.0)
        await menu.start(ctx)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @commands.command(name="charinfo")
    async def command_charinfo(self, ctx: commands.Context, *, characters: str):
        if len(characters) > 15:
            return await ctx.send("You can only pass 15 characters at a time.")

        names = []
        points = []

        for c in characters:
            digit = f"{ord(c):x}".upper()
            name = unicodedata.name(c, "N/A")
            names.append(f"[{name}](https://fileformat.info/info/unicode/char/{digit})")
            points.append(f"U+{digit:>04}")

        embed = discord.Embed.from_dict(
            {
                "title": "Character information",
                "description": f"Displaying information on {len(characters)} character(s).",
                "color": DEFAULT_EMBED_COLOUR,
                "author": {"name": "Query"},
                "footer": {"text": f"Requested by {ctx.author.display_name}", "icon_url": f"{ctx.author.avatar_url}",},
                "fields": [
                    {"name": "Names", "value": "\n".join(names), "inline": True},
                    {"name": "Code points", "value": "\n".join(points), "inline": True},
                ],
            }
        )

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Miscellaneous(bot))
