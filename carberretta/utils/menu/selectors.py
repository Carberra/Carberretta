from asyncio import TimeoutError
from datetime import timedelta

from carberretta.utils import chron
from carberretta.utils.emoji import ALTERNATIVES


class Selector:
    def __init__(self, menu, selection, *, timeout=300.0, auto_exit=True, check=None):
        self.menu = menu
        self.timeout = timeout
        self.auto_exit = auto_exit
        self.check = check or self._default_check

        self._base_selection = selection

    @property
    def selection(self):
        return self._base_selection

    @selection.setter
    def selection(self, value):
        self._base_selection = value

    def _default_check(self, reaction, user):
        return (
            reaction.message.id == self.menu.message.id
            and user == self.menu.ctx.author
            and self._resolve_selection(reaction.emoji) in self.selection
        )

    def _resolve_selection(self, emoji):
        if isinstance(emoji, str):
            for name, value in ALTERNATIVES.items():
                if value == emoji:
                    return name
        elif hasattr(emoji, "name"):
            return emoji.name

    async def _serve(self):
        await self.menu.message.clear_reactions()

        for e in self.selection:
            await self.menu.message.add_reaction(self.menu.bot.emoji.get(e))

    async def response(self):
        await self._serve()

        try:
            reaction, user = await self.menu.bot.wait_for("reaction_add", timeout=self.timeout, check=self.check)
        except TimeoutError:
            await self.menu.timeout(chron.long_delta(timedelta(seconds=self.timeout)))
        else:
            r = self._resolve_selection(reaction.emoji)
            if r == "exit" and self.auto_exit:
                await self.menu.stop()
            else:
                return r

    def __repr__(self):
        return (
            f"<Selector"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" menu={self.menu!r}>"
        )


class NumericalSelector(Selector):
    def __init__(self, menu, iterable, *, timeout=300.0, auto_exit=True, check=None):
        super().__init__(menu, ["exit"], timeout=timeout, auto_exit=auto_exit, check=check)

        self.iterable = iterable
        self.max_page = (len(iterable) // 9) + 1
        self.pages = [{} for i in range(self.max_page)]

        self._selection = []
        self._last_selection = []
        self._page = 0

        for i, obj in enumerate(iterable):
            self.pages[i // 9].update({f"option{(i % 9) + 1}": obj})

    @property
    def selection(self):
        return self._selection

    @selection.setter
    def selection(self, value):
        self._last_selection = self._selection
        self._selection = value

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        self._page = max(0, min(value, self.max_page - 1))

    @property
    def last_selection(self):
        return self._last_selection

    @property
    def page_info(self):
        return f"Page {self.page + 1:,} of {self.max_page:,}"

    @property
    def table(self):
        return "\n".join(f"{self.menu.bot.emoji.mention(k)} {v}" for k, v in self.pages[self.page].items())

    def set_selection(self):
        s = self._base_selection.copy()
        insert_point = 0

        if len(self.pages) > 1:
            if self.page != 0:
                s.insert(0, "pageback")
                s.insert(0, "stepback")
                insert_point += 2

            if self.page != self.max_page - 1:
                s.insert(insert_point, "stepnext")
                s.insert(insert_point, "pagenext")

        for i in range(len(self.pages[self.page])):
            s.insert(i + insert_point, f"option{i + 1}")

        self.selection = s

    async def response(self):
        self.set_selection()

        if self.selection != self.last_selection:
            await self._serve()

        try:
            reaction, user = await self.menu.bot.wait_for("reaction_add", timeout=self.timeout, check=self.check)
        except TimeoutError:
            await self.menu.timeout(chron.long_delta(timedelta(seconds=self.timeout)))
        else:
            r = self._resolve_selection(reaction.emoji)
            if r == "exit":
                if self.auto_exit:
                    await self.menu.stop()
                return
            elif r == "stepback":
                self.page = 0
            elif r == "pageback":
                self.page -= 1
            elif r == "pagenext":
                self.page += 1
            elif r == "stepnext":
                self.page = self.max_page
            else:
                return self.pages[self.page][r]

            await self.menu.switch(reaction)
            return await self.response()

    def __repr__(self):
        return (
            f"<NumericalSelector"
            f" page={self.page!r}"
            f" max_page={self.max_page!r}"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" menu={self.menu!r}>"
        )


class PageControls(Selector):
    def __init__(self, menu, pagemaps, *, timeout=300.0, auto_exit=True, check=None):
        super().__init__(menu, ["exit"], timeout=timeout, auto_exit=auto_exit, check=check)

        self.pagemaps = pagemaps
        self.max_page = len(pagemaps)

        self._selection = []
        self._last_selection = []
        self._page = 0

    @property
    def selection(self):
        return self._selection

    @selection.setter
    def selection(self, value):
        self._last_selection = self._selection
        self._selection = value

    @property
    def page(self):
        return self._page

    @page.setter
    def page(self, value):
        self._page = max(0, min(value, self.max_page - 1))

    @property
    def last_selection(self):
        return self._last_selection

    @property
    def page_info(self):
        return f"Page {self.page + 1:,} of {self.max_page:,}"

    def set_selection(self):
        s = self._base_selection.copy()
        insert_point = 0

        if len(self.pagemaps) > 1:
            if self.page != 0:
                s.insert(0, "pageback")
                s.insert(0, "stepback")
                insert_point += 2

            if self.page != self.max_page - 1:
                s.insert(insert_point, "stepnext")
                s.insert(insert_point, "pagenext")

        self.selection = s

    async def response(self):
        self.set_selection()

        if self.selection != self.last_selection:
            await self._serve()

        try:
            reaction, user = await self.menu.bot.wait_for("reaction_add", timeout=self.timeout, check=self.check)
        except TimeoutError:
            await self.menu.timeout(chron.long_delta(timedelta(seconds=self.timeout)))
        else:
            r = self._resolve_selection(reaction.emoji)
            if r == "exit":
                if self.auto_exit:
                    await self.menu.stop()
                return
            elif r == "stepback":
                self.page = 0
            elif r == "pageback":
                self.page -= 1
            elif r == "pagenext":
                self.page += 1
            elif r == "stepnext":
                self.page = self.max_page

            await self.menu.switch(reaction)
            return await self.response()

    def __repr__(self):
        return (
            f"<PageControls"
            f" page={self.page!r}"
            f" max_page={self.max_page!r}"
            f" timeout={self.timeout!r}"
            f" auto_exit={self.auto_exit!r}"
            f" check={self.check!r}"
            f" menu={self.menu!r}>"
        )
