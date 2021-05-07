from discord.ext.commands import Converter


class Command(Converter):
    async def convert(self, ctx, arg):
        return ctx.bot.get_command(arg)
