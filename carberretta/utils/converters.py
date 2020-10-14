from discord.ext import commands


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
