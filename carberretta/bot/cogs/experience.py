import typing as t
from math import ceil
from random import randint

import discord
from discord.ext import commands

from carberretta.utils import DEFAULT_EMBED_COLOUR


class Experience(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @staticmethod
    def calc_lvl(exp: int) -> int:
        return ceil((exp / 42) ** 0.55)

    @staticmethod
    def calc_required_exp(lvl: int) -> int:
        return ceil((lvl ** (1 / 0.55)) * 42)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        # xp add values can change
        # 60 seconds can change
        exp: int
        lvl: int
        lvl_msg: int
        exp, lvl, lvl_msg = await self.bot.db.record(
            (
                "INSERT INTO members(UserID) "
                "VALUES(?) "
                "ON CONFLICT(UserID) DO UPDATE SET "
                "Experience = Experience + (CASE WHEN NextUpdate < CURRENT_TIMESTAMP THEN ? ELSE 0 END), "
                "NextUpdate = (CASE WHEN NextUpdate < CURRENT_TIMESTAMP THEN DATETIME(CURRENT_TIMESTAMP, '+60 seconds') ELSE NextUpdate END) "
                "WHERE UserID = ? "
                "RETURNING Experience, Level, LevelMessage"
            ),
            message.author.id,
            randint(1, 20),
            message.author.id,
        )
        new_lvl: int
        if (new_lvl := self.calc_lvl(exp)) > lvl:
            await self.bot.db.execute(
                "UPDATE members SET Level = ? WHERE UserID = ?",
                new_lvl,
                message.author.id,
            )
            if lvl_msg:
                await message.reply(
                    f"{message.author.display_name}, you leveled up! You are now level {new_lvl}.",
                    delete_after=10,
                    mention_author=False,
                )

    @commands.command(name="level", aliases=["lvl", "rank", "experience", "exp", "xp"])
    async def command_level(self, ctx: commands.Context, member: t.Optional[discord.Member]) -> None:
        member: discord.Member = member or ctx.author
        exp: t.Optional[int] = await self.bot.db.field("SELECT Experience FROM members WHERE UserID = ?", member.id)
        if exp is None:
            return await ctx.send(f"{member.display_name} is not in the database.")
        lvl: int = self.calc_lvl(exp)
        required_exp: int = self.calc_required_exp(lvl)
        await ctx.send(f"{member.display_name} is on level {lvl}. Progress to next level: ({exp}/{required_exp}).")

    @commands.command(
        name="togglelevelmessage",
        aliases=["togglelvlmsg", "lvluplog", "lvlupmsg"],
    )
    async def command_togglelevelmessage(self, ctx: commands.Context) -> None:
        changed_to: t.Optional[int] = await self.bot.db.field(
            "UPDATE members SET LevelMessage = (CASE LevelMessage WHEN 1 THEN 0 ELSE 1 END) WHERE UserID = ? RETURNING LevelMessage",
            ctx.author.id,
        )
        if changed_to is None:
            return await ctx.send("You are not in the database.")
        await ctx.send(f"Turned level up messages {'on' if changed_to else 'off'}.")

    @commands.command(
        name="leveltop",
        aliases=[
            "ranktop",
            "lvltop",
            "experiencetop",
            "exptop",
            "xptop" "levellb",
            "ranklb",
            "lvllb",
            "experiencelb",
            "explb",
            "xplb",
        ],
    )
    async def command_leveltop(self, ctx: commands.Context) -> None:
        leaderboard: t.List[t.Tuple[int, int]] = await self.bot.db.records(
            "SELECT UserID, Experience FROM members ORDER BY Experience DESC LIMIT 10"
        )

        if len(leaderboard) == 0:
            return await ctx.send("No one is in the database yet.")

        embed: discord.Embed = discord.Embed.from_dict(
            {
                "title": "Experience Leaderboard",
                "color": DEFAULT_EMBED_COLOUR,
                "description": "\n".join(
                    [
                        f"{i + 1}. {self.bot.get_user(member[0]).display_name}, level {self.calc_lvl(member[1])}, experience {member[1]}."
                        for i, member in enumerate(leaderboard)
                    ]
                ),
                "thumbnail": {"url": f"{self.bot.get_user(leaderboard[0][0]).avatar_url}"},
                "footer": {"text": f"Showing top {len(leaderboard)}."},
            }
        )

        await ctx.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Experience(bot))
