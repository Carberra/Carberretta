from discord.ext.commands import CommandError


class WordAlreadyAdded(CommandError):
    def __init__(self, found):
        self.found = found


class WordNotFound(CommandError):
    def __init__(self, found):
        self.found = found


class InvalidAction(CommandError):
    def __init__(self, action, action_types):
        self.action = action
        self.action_types = action_types
