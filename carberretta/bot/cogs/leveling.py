import typing
from datetime import datetime
from math import ceil
from random import randint

import discord
from dateutil.parser import parse
from discord.ext import commands

from carberretta.utils import DEFAULT_EMBED_COLOUR


class Leveling(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def calculate_level(exp: int) -> int:
        return ceil((exp / 42) ** 0.55)

    @staticmethod
    def calculate_next_level(lvl: int) -> int:
        return ceil((lvl ** (1 / .55)) * 42)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        last_updated = await self.bot.db.field("SELECT LastUpdate FROM users WHERE UserID = ?", message.author.id)
        if (datetime.utcnow() - parse(last_updated)).seconds < 60:  # 60 seconds can change
            return

        # xp add values can change
        await self.bot.db.execute(
            "UPDATE users SET Experience = Experience + ?, LastUpdate = CURRENT_TIMESTAMP WHERE UserID = ?",
            randint(1, 20), message.author.id)
        exp, lvl, lvl_msg = await self.bot.db.record(
            "SELECT Experience, Level, LevelMessage FROM users WHERE UserID = ?", message.author.id)
        if (new_lvl := self.calculate_level(exp)) > lvl:
            await self.bot.db.execute("UPDATE users SET Level = ? WHERE UserID = ?", new_lvl, message.author.id)
            if lvl_msg:
                await message.reply(f"{message.author.display_name}, you leveled up! You are now level `{new_lvl}`.",
                                    delete_after=10, mention_author=False)

    @commands.command(name="experience", aliases=["exp", "xp"])
    async def experience_command(self, ctx: commands.Context, user: typing.Optional[commands.MemberConverter]) -> None:
        user = user or ctx.author
        exp = await self.bot.db.field("SELECT Experience FROM users WHERE UserID = ?", user.id)
        if exp is None:
            await ctx.send(f"{user.display_name} is not in the database.")
            return
        await ctx.send(f"{user.display_name} has `{exp}` experience.")

    @commands.command(name="level", aliases=["lvl", "rank"])
    async def level_command(self, ctx: commands.Context, user: typing.Optional[commands.MemberConverter]) -> None:
        user = user or ctx.author
        exp = await self.bot.db.field("SELECT Experience FROM users WHERE UserID = ?", user.id)
        if exp is None:
            await ctx.send(f"{user.display_name} is not in the database.")
            return
        lvl = self.calculate_level(exp)
        next_at = self.calculate_next_level(lvl)
        await ctx.send(f"{user.display_name} has `{lvl}` levels. (`{exp}/{next_at}`)")

    @commands.command(name="togglelevelmessage", aliases=["togglelvlmsg", "lvluplog"])
    async def togglelevelmessage_command(self, ctx: commands.Context):
        before = await self.bot.db.field("SELECT LevelMessage FROM users WHERE UserID = ?", ctx.author.id)
        await self.bot.db.execute("UPDATE users SET LevelMessage = ? WHERE UserID = ?", int(not before), ctx.author.id)
        await ctx.send(f"Turned level up messages {'off' if before else 'on'}.")

    @commands.command(name="leveltop", aliases=["ranktop", "lvltop", "experiencetop", "exptop", "xptop"])
    async def leveltop_command(self, ctx: commands.Context):
        leaderboard = await self.bot.db.records(
            "SELECT UserID, Level, Experience FROM users ORDER BY Experience DESC LIMIT 10")

        embed = discord.Embed.from_dict({
            "title": "Experience Leaderboard",
            "color": DEFAULT_EMBED_COLOUR,
            "description": "\n".join(
                [f"{i + 1}. {self.bot.get_user(user[0]).display_name}, level `{user[1]}`, experience `{user[2]}`." for
                 i, user in enumerate(leaderboard)]),
            "thumbnail": {"url": f"{self.bot.get_user(leaderboard[0][0]).avatar_url}"},
            "footer": {"text": f"Showing top {len(leaderboard)}."}
        })

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Leveling(bot))
