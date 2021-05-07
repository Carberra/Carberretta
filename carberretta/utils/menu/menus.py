import discord

from carberretta.utils.menu import selectors


class Menu:
    def __init__(self, ctx, pagemap, *, delete_after=False, delete_invoke_after=None):
        self.ctx = ctx
        self.bot = ctx.bot
        self.pagemap = pagemap
        self.delete_after = delete_after
        self.delete_invoke_after = delete_invoke_after or delete_after

    async def start(self):
        self.message = await self.ctx.send(
            embed=discord.Embed.from_dict(
                {
                    "footer": {
                        "text": f"Requested by {self.ctx.author.display_name}",
                        "icon_url": f"{self.ctx.author.avatar_url}",
                    },
                    **self.pagemap,
                }
            )
        )

    async def stop(self):
        if self.delete_after:
            await self.message.delete()
        else:
            await self.message.clear_reactions()
            await self.message.edit(content=f"The interactive menu was closed.", embed=None)

        if self.delete_invoke_after:
            await self.ctx.message.delete()

    async def timeout(self, length):
        if self.delete_after:
            await self.message.delete()
        else:
            await self.message.clear_reactions()
            await self.message.edit(
                content=f"The interactive menu timed out as there was no user interation for {length}.", embed=None,
            )

        if self.delete_invoke_after:
            await self.ctx.message.delete()

    async def switch(self, pagemap=None, clear_reactions=False):
        if clear_reactions:
            await self.message.clear_reactions()

        await self.message.edit(embed=discord.Embed.from_dict(pagemap or self.pagemap))

    def __repr__(self):
        return (
            f"<Menu"
            f" delete_after={self.delete_after!r}"
            f" delete_invoke_after={self.delete_invoke_after!r}"
            f" message={self.message!r}>"
        )


class SelectionMenu(Menu):
    def __init__(
        self,
        ctx,
        selection,
        pagemap,
        *,
        delete_after=False,
        delete_invoke_after=None,
        timeout=300.0,
        auto_exit=True,
        check=None,
    ):
        super().__init__(ctx, pagemap, delete_after=delete_after, delete_invoke_after=delete_invoke_after)
        self.selector = selectors.Selector(self, selection, timeout=timeout, auto_exit=auto_exit, check=check)

    async def start(self):
        await super().start()
        return await self.selector.response()

    def __repr__(self):
        return (
            f"<SelectionMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" delete_after={self.delete_after!r}"
            f" delete_invoke_after={self.delete_invoke_after!r}"
            f" message={self.message!r}>"
        )


class NumberedSelectionMenu(Menu):
    def __init__(
        self,
        ctx,
        iterable,
        pagemap,
        *,
        delete_after=False,
        delete_invoke_after=None,
        timeout=300.0,
        auto_exit=True,
        check=None,
    ):
        super().__init__(ctx, pagemap, delete_after=delete_after, delete_invoke_after=delete_invoke_after)
        self.selector = selectors.NumericalSelector(self, iterable, timeout=timeout, auto_exit=auto_exit, check=check)

    @property
    def page_field(self):
        return {"name": self.selector.page_info, "value": self.selector.table, "inline": False}

    async def start(self):
        self.pagemap.update({"fields": [self.page_field]})
        await super().start()
        return await self.selector.response()

    async def switch(self, reaction):
        self.pagemap.update({"fields": [self.page_field]})
        await super().switch()
        await self.message.remove_reaction(reaction, self.ctx.author)

    def __repr__(self):
        return (
            f"<NumberedSelectionMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" delete_after={self.delete_after!r}"
            f" delete_invoke_after={self.delete_invoke_after!r}"
            f" message={self.message!r}>"
        )


class MultiPageMenu(Menu):
    def __init__(
        self, ctx, pagemaps, *, delete_after=False, delete_invoke_after=None, timeout=300.0, auto_exit=True, check=None
    ):
        super().__init__(ctx, pagemaps[0], delete_after=delete_after, delete_invoke_after=delete_invoke_after)
        self.selector = selectors.PageControls(self, pagemaps, timeout=timeout, auto_exit=auto_exit, check=check)

    async def start(self):
        await super().start()
        return await self.selector.response()

    async def switch(self, reaction):
        await super().switch(self.selector.pagemaps[self.selector.page])
        await self.message.remove_reaction(reaction, self.ctx.author)

    def __repr__(self):
        return (
            f"<MultiPageMenu"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" delete_after={self.delete_after!r}"
            f" delete_invoke_after={self.delete_invoke_after!r}"
            f" message={self.message!r}>"
        )
