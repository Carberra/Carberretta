from discord.ext import commands

from carberretta import Config


class CustomCheckFailure(commands.CheckAnyFailure):
    def __init__(self, message):
        self.msg = message


class CanNotVerifyQt(CustomCheckFailure):
    def __init__(self):
        super().__init__("You can not verify QTs.")


def can_verify_qts():
    async def predicate(ctx):
        if ctx.message.author.id != Config.QT_ID:
            raise CanNotVerifyQt()
        return True

    return commands.check(predicate)
