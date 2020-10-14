import datetime as dt
import typing as t
from collections import defaultdict

import discord
from discord.ext import commands

from carberretta import Config
from carberretta.utils import DEFAULT_EMBED_COLOUR, chron, converters, menu, string


class HelpMenu(menu.MultiPageMenu):
    def __init__(self, ctx, pagemaps):
        super().__init__(ctx, pagemaps, timeout=120.0)


class Help(commands.Cog):
    """This cog. Provides help with Carberretta's commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        bot.remove_command("help")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @staticmethod
    async def basic_syntax(ctx: commands.Context, cmd: commands.Command) -> str:
        try:
            await cmd.can_run(ctx)
            return f"{Config.PREFIX}{cmd.name}" if cmd.parent is None else f"  ↳ {cmd.name}"
        except commands.CommandError:
            return f"{Config.PREFIX}{cmd.name} (✗)" if cmd.parent is None else f"  ↳ {cmd.name} (✗)"

    @staticmethod
    def full_syntax(cmd: commands.Command) -> str:
        invokations = "|".join([cmd.name, *cmd.aliases])
        if (p := cmd.parent) is None:
            return f"```{Config.PREFIX}{invokations} {cmd.signature}```"
        else:
            p_invokations = "|".join([p.name, *p.aliases])
            return f"```{Config.PREFIX}{p_invokations} {invokations} {cmd.signature}```"

    @staticmethod
    async def required_permissions(ctx: commands.Context, cmd: commands.Command) -> str:
        try:
            await cmd.can_run(ctx)
            return "Yes"
        except commands.MissingPermissions as exc:
            mp = string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms])
            return f"No - You are missing the {mp} permission(s)"
        except commands.BotMissingPermissions as exc:
            mp = string.list_of([str(perm.replace("_", " ")).title() for perm in exc.missing_perms])
            return f"No - Carberretta is missing the {mp} permission(s)"
        except commands.CommandError:
            return "No"

    async def get_command_mapping(self) -> t.Mapping[commands.Cog, list]:
        mapping = defaultdict(list)

        for cog in self.bot.cogs.values():
            if cog.__doc__ is not None:
                for cmd in cog.walk_commands():
                    if cmd.help is not None:
                        mapping[cog].append(cmd)

        return mapping

    @commands.command(
        name="help",
        help="This command. Passing a command name or alias through will show help with that specific command, while passing no arguments will bring up a general command overview.",
    )
    async def help_command(self, ctx: commands.Context, *, cmd: t.Optional[t.Union[converters.Command, str]]) -> None:
        if isinstance(cmd, str):
            return await ctx.send("Carberretta has no commands or aliases with that name.")

        if isinstance(cmd, commands.Command):
            return await ctx.send(
                embed=discord.Embed.from_dict(
                    {
                        "title": f"The `{cmd.name}` command",
                        "description": cmd.help,
                        "color": DEFAULT_EMBED_COLOUR,
                        "thumbnail": {"url": f"{self.bot.user.avatar_url}"},
                        "author": {"name": "Help"},
                        "footer": {
                            "text": f"Requested by {ctx.author.display_name}",
                            "icon_url": f"{ctx.author.avatar_url}",
                        },
                        "fields": [
                            {
                                "name": "Syntax (<required> • [optional])",
                                "value": self.full_syntax(cmd),
                                "inline": False,
                            },
                            {
                                "name": "On cooldown?",
                                "value": (
                                    f"Yes, for {chron.long_delta(dt.timedelta(seconds=s))}."
                                    if (s := cmd.get_cooldown_retry_after(ctx))
                                    else "No"
                                ),
                                "inline": False,
                            },
                            {
                                "name": "Can be run?",
                                "value": await self.required_permissions(ctx, cmd),
                                "inline": False,
                            },
                            {
                                "name": "Parent",
                                "value": self.full_syntax(p) if (p := cmd.parent) is not None else "None",
                                "inline": False,
                            },
                        ],
                    }
                )
            )

        pagemaps = []

        for cog, cmds in (await self.get_command_mapping()).items():
            pagemaps.append(
                {
                    "title": f"{cog.qualified_name} commands",
                    "description": f"{cog.__doc__}\n\nUse `{Config.PREFIX}help [command]` for more detailed information on a command. You can not run commands with `(✗)` next to them.",
                    "color": DEFAULT_EMBED_COLOUR,
                    "thumbnail": {"url": f"{self.bot.user.avatar_url}"},
                    "author": {"name": "Help"},
                    "footer": {
                        "text": f"Requested by {ctx.author.display_name}",
                        "icon_url": f"{ctx.author.avatar_url}",
                    },
                    "fields": [
                        {
                            "name": f"{len(cmds)} command(s)",
                            "value": "```{}```".format("\n".join([await self.basic_syntax(ctx, cmd) for cmd in cmds])),
                            "inline": False,
                        }
                    ],
                }
            )

        await HelpMenu(ctx, pagemaps).start()


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Help(bot))
