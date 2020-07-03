class Ready:
    def __init__(self, bot):
        self.bot = bot
        self.booted = False

        for cog in self.bot._cogs:
            setattr(self, cog, False)

    def up(self, cog):
        setattr(self, (qn := cog.qualified_name.lower()), True)
        print(f" {qn} cog ready")

    @property
    def all(self):
        return self.bot and all([getattr(self, cog) for cog in self.bot.cogs])
