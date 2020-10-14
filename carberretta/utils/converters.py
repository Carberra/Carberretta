import discord
from discord.ext import commands

from carberretta.utils import Search


class Command(commands.Converter):
    async def convert(self, ctx, arg):
        if (c := ctx.bot.get_command(arg)) is not None:
            return c

        # Check for subcommands.
        for cmd in ctx.bot.walk_commands():
            if arg == f"{cmd.parent.name} {cmd.name}":
                return cmd

        # Nothing found.
        raise commands.BadArgument


class SearchedMember(commands.Converter):
    async def convert(self, ctx, arg):
        if (
            member := discord.utils.get(
                ctx.guild.members,
                name=str(Search(arg, [m.display_name for m in ctx.guild.members]).best(min_accuracy=0.75)),
            )
        ) is None:
            raise commands.BadArgument
        return member
