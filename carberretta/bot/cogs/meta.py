"""
META

Self:
    About;
    Bot info;
    Help;
    Source.
"""

import os
import typing as t
from datetime import datetime, timedelta
from inspect import getsourcelines
from os.path import relpath
from platform import python_version
from subprocess import check_output
from sys import platform
from time import time

import discord
from discord.ext import commands
from github import Github, Issue, UnknownObjectException
from psutil import Process, virtual_memory
from pygount import SourceAnalysis

from carberretta import Config
from carberretta.utils import DEFAULT_EMBED_COLOUR, ROOT_DIR, chron, converters, menu


async def issue_embed(issue: Issue.Issue, issue_number: int, author: discord.Member) -> dict:
    issue_open = "Open"
    issue_color = 0x17A007
    issue_body = "*No description provided.*"
    issue_status = "Unknown"
    issue_types = []
    issue_type_label = "Type"
    issue_milestone = "None"
    issue_creator = issue.user.login

    if issue.closed_at:
        issue_open = "Closed"
        issue_color = DEFAULT_EMBED_COLOUR

    if issue.body:
        issue_body = issue.body

    if len(issue.body) > 300:
        issue_body = f"{issue.body[:300]}..."

        if issue.body[299] == " ":
            issue_body = f"{issue.body[:299]}..."

    for label in issue.labels:
        if label.name.startswith("status/"):
            issue_status = label.name[7:].capitalize()
            continue

        if label.name.startswith("type/"):
            issue_types.append(label.name[5:].capitalize())
            continue

    if issue.milestone:
        issue_milestone = issue.milestone.title

    if issue.user.name:
        issue_creator = f"{issue.user.name} ({issue.user.login})"

    if len(issue_types) > 1:
        issue_type_label = "Types"

    if not len(issue_types) > 0:
        issue_types = ["Unknown"]

    return {
        "title": f"{issue_open}: {issue.title} (#{issue.number})",
        "description": f"Click [here](https://github.com/Carberra/Carberretta/issues/{issue_number}) to view on the web version.",
        "color": issue_color,
        "author": {"name": "Query"},
        "footer": {"text": f"Requested by {author.display_name}", "icon_url": f"{author.avatar_url}",},
        "fields": [
            {"name": "Description", "value": issue_body, "inline": False},
            {"name": "Status", "value": issue_status, "inline": True},
            {"name": issue_type_label, "value": ", ".join(issue_types), "inline": True},
            {"name": "Milestone", "value": issue_milestone, "inline": True},
            {"name": "Created by", "value": issue_creator, "inline": True},
            {"name": "Created at", "value": chron.long_date(issue.created_at), "inline": True},
            {"name": "Existed for", "value": chron.short_delta(datetime.utcnow() - issue.created_at), "inline": True,},
        ],
    }


class SearchMenu(menu.NumberedSelectionMenu):
    def __init__(self, ctx, data, results, pagemap):
        self.data = data
        super().__init__(ctx, results, pagemap)

    async def start(self):
        if (r := await super().start()) is not None:
            await self.display_issue(r)

    async def display_issue(self, name):
        for issue in self.data:
            if f"{issue.title} (#{issue.number})" == name:
                await self.message.clear_reactions()
                await self.message.edit(
                    embed=discord.Embed.from_dict(await issue_embed(issue, issue.number, self.ctx.author))
                )


class Meta(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        # self.bot.remove_command("help")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.gh = Github(Config.GITHUB_API_TOKEN)
            self.bot.ready.up(self)

    @commands.command(name="about")
    async def command_about(self, ctx: commands.Context) -> None:
        await ctx.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "About Carberretta",
                    "description": "Type `+info` for bot stats.",
                    "color": DEFAULT_EMBED_COLOUR,
                    "thumbnail": {"url": f"{self.bot.user.avatar_url}"},
                    "author": {"name": "Carberretta"},
                    "footer": {
                        "text": f"Requested by {ctx.author.display_name}",
                        "icon_url": f"{ctx.author.avatar_url}",
                    },
                    "fields": [
                        {
                            "name": "Authors",
                            "value": "\n".join(f"<@{id_}>" for id_ in Config.OWNER_IDS),
                            "inline": False,
                        },
                        {
                            "name": "Source",
                            "value": "Click [here](https://github.com/Carberra/Carberretta)",
                            "inline": False,
                        },
                        {
                            "name": "License",
                            "value": "[BSD 3-Clause](https://github.com/Carberra/Carberretta/blob/master/LICENSE)",
                            "inline": False,
                        },
                    ],
                }
            )
        )

    # @commands.command(name="help")
    # async def command_help(self, ctx: commands.Context, command: t.Optional[commands.Command]) -> None:
    #     """This command. Invoke without any arguments for full help."""
    #     print(command)
    #     if command is None:
    #         pass
    #     else:
    #         syntax = f"{'|'.join([str(command), *command.aliases])} {command.signature}"

    #         await ctx.send(
    #             embed=discord.Embed.from_dict(
    #                 {
    #                     "title": f"Help with `{command.name}`",
    #                     "description": command.help or "Not available.",
    #                     "colour": DEFAULT_EMBED_COLOUR,
    #                     "thumbnail": {"url": f"{ctx.guild.icon_url}"},
    #                     "author": {"name": "Carberretta"},
    #                     "footer": {
    #                         "text": f"Requested by {ctx.author.display_name}",
    #                         "icon_url": f"{ctx.author.avatar_url}",
    #                     },
    #                     "fields": [{"name": "Syntax", "value": f"```+{syntax}```", "inline": False}],
    #                 }
    #             )
    #         )

    @commands.command(name="botinfo", aliases=("bi", "info"))
    async def command_bot_info(self, ctx: commands.Context) -> None:
        proc = Process()
        with proc.oneshot():
            uptime = chron.short_delta(timedelta(seconds=time() - proc.create_time()))
            cpu_time = chron.short_delta(
                timedelta(seconds=(cpu := proc.cpu_times()).system + cpu.user), milliseconds=True
            )
            mem_total = virtual_memory().total / (1024 ** 2)
            mem_of_total = proc.memory_percent()
            mem_usage = mem_total * (mem_of_total / 100)

        await ctx.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "Carberretta Information",
                    "color": DEFAULT_EMBED_COLOUR,
                    "thumbnail": {"url": f"{self.bot.user.avatar_url}"},
                    "author": {"name": "Carberretta"},
                    "footer": {
                        "text": f"Requested by {ctx.author.display_name}",
                        "icon_url": f"{ctx.author.avatar_url}",
                    },
                    "fields": [
                        {"name": "Bot Version", "value": self.bot.version, "inline": True},
                        {"name": "Python Version", "value": python_version(), "inline": True},
                        {"name": "discord.py Version", "value": discord.__version__, "inline": True},
                        {"name": "Uptime", "value": uptime, "inline": True},
                        {"name": "CPU Time", "value": cpu_time, "inline": True},
                        {
                            "name": "Memory Usage",
                            "value": f"{mem_usage:,.3f} / {mem_total:,.0f} MiB ({mem_of_total:,.0f}%)",
                            "inline": True,
                        },
                        {"name": "Code Lines", "value": f"{int(self.bot.loc.code):,}", "inline": True},
                        {"name": "Docs Lines", "value": f"{int(self.bot.loc.docs):,}", "inline": True},
                        {"name": "Blank Lines", "value": f"{int(self.bot.loc.empty):,}", "inline": True},
                        {"name": "Database Calls", "value": f"{self.bot.db._calls:,}", "inline": True},
                    ],
                }
            )
        )

    @commands.command(name="source")
    async def command_source(self, ctx: commands.Context, command: t.Optional[converters.Command]) -> None:
        source_url = "https://github.com/Carberra/Carberretta"

        if command is None:
            await ctx.send(f"<{source_url}>")
        else:
            src = command.callback.__code__
            module = command.callback.__module__
            filename = src.co_filename
            lines, firstlineno = getsourcelines(src)

            if not module.startswith("discord"):
                location = relpath(filename).replace("\\", "/")
            else:
                source_url = "https://github.com/Rapptz/discord.py"
                location = module.replace(".", "/") + ".py"

            await ctx.send(f"<{source_url}/blob/master/{location}#L{firstlineno}-L{firstlineno + len(lines) - 1}>")

    @commands.command(name="issue")
    async def command_issue(self, ctx: commands.Context, *, issue_query: str) -> None:
        try:
            issue_number = int(issue_query.lstrip("#"))

            try:
                issue = self.gh.get_repo("Carberra/Carberretta").get_issue(number=issue_number)
            except UnknownObjectException:
                await ctx.send("Invalid issue number.")
                return

            await ctx.send(embed=discord.Embed.from_dict(await issue_embed(issue, issue_number, ctx.author)))

        except ValueError:
            data = self.gh.search_issues(f"{issue_query} is:issue repo:Carberra/Carberretta")

            pagemap = {
                "title": "Search results",
                "description": f"{data.totalCount} result(s).",
                "color": DEFAULT_EMBED_COLOUR,
                "author": {"name": "Query"},
                "footer": {"text": f"Requested by {ctx.author.display_name}", "icon_url": f"{ctx.author.avatar_url}",},
            }
            results = [f"{issue.title} (#{issue.number})" for issue in data if not issue.closed_at] + [
                f"{issue.title} (#{issue.number})" for issue in data if issue.closed_at
            ]

            if not results:
                return await ctx.send("No results found. Are you sure that's an issue for Carberretta?")

            if not len(results) > 1:
                return await ctx.send(
                    embed=discord.Embed.from_dict(await issue_embed(data[0], data[0].number, ctx.author))
                )

            await SearchMenu(ctx, data, results, pagemap).start()

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown_command(self, ctx: commands.Context) -> None:
        # Prefer hub shutdown where possible.
        await ctx.message.delete()
        await self.bot.close()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Meta(bot))
