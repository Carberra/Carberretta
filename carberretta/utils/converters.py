import discord
from discord.ext import commands

from carberretta.utils import Search


class Command(commands.Converter):
    async def convert(self, ctx, arg):
        return ctx.bot.get_command(arg)


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
