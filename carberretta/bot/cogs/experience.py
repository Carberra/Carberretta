import typing
from datetime import datetime
from math import ceil
from random import randint

import discord
from discord.ext import commands

from carberretta.utils import DEFAULT_EMBED_COLOUR


class Experience(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @staticmethod
    def calc_lvl(exp: int) -> int:
        return ceil((exp / 42) ** 0.55)

    @staticmethod
    def calc_next_lvl_at(lvl: int) -> int:
        return ceil((lvl ** (1 / .55)) * 42)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        # xp add values can change
        exp, lvl, lvl_msg = await self.bot.db.record("""
                                                     INSERT INTO users(UserID)
                                                     VALUES(?)
                                                     ON CONFLICT(UserID) DO UPDATE SET
                                                     Experience=Experience + (CASE WHEN ROUND((JULIANDAY(CURRENT_TIMESTAMP) - JULIANDAY(LastUpdate)) * 86400) > 60 THEN ? ELSE 0 END),
                                                     LastUpdate=CURRENT_TIMESTAMP
                                                     WHERE UserID= ?
                                                     RETURNING Experience, Level, LevelMessage""", message.author.id, randint(1, 20), message.author.id)
        if (new_lvl := self.calc_lvl(exp)) > lvl:
            await self.bot.db.execute("UPDATE users SET Level = ? WHERE UserID = ?", new_lvl, message.author.id)
            if lvl_msg:
                await message.reply(f"{message.author.display_name}, you leveled up! You are now level `{new_lvl}`.",
                                    delete_after=10, mention_author=False)

    @commands.command(name="level", aliases=["lvl", "rank", "experience", "exp", "xp"])
    async def command_level(self, ctx: commands.Context, user: typing.Optional[commands.MemberConverter]) -> None:
        user = user or ctx.author
        exp = await self.bot.db.field("SELECT Experience FROM users WHERE UserID = ?", user.id)
        if exp is None:
            await ctx.send(f"{user.display_name} is not in the database.")
            return
        lvl = self.calc_lvl(exp)
        next_at = self.calc_next_lvl_at(lvl)
        await ctx.send(f"{user.display_name} has `{lvl}` levels. (`{exp}/{next_at}`)")

    @commands.command(name="togglelevelmessage", aliases=["togglelvlmsg", "lvluplog"])
    async def command_togglelevelmessage(self, ctx: commands.Context):
        changed_to = await self.bot.db.field("UPDATE users SET LevelMessage = (CASE LevelMessage WHEN 1 THEN 0 ELSE 1 END) WHERE UserID = ? RETURNING LevelMessage", ctx.author.id)
        await ctx.send(f"Turned level up messages {'on' if changed_to else 'off'}.")

    @commands.command(name="leveltop", aliases=["ranktop", "lvltop", "experiencetop", "exptop", "xptop"])
    async def command_leveltop(self, ctx: commands.Context):
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
    bot.add_cog(Experience(bot))
