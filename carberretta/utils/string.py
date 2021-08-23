import re
import typing as t

from aiohttp import ClientSession
from discord import Member, User

from string import Formatter

ORDINAL_ENDINGS: t.Final = {"1": "st", "2": "nd", "3": "rd"}


class MessageFormatter(Formatter):
    def get_value(self, key: t.Union[int, str], args: t.Sequence[t.Any], kwargs: t.Mapping[str, t.Any]) -> str:
        if isinstance(key, str):
            try:
                return kwargs[key]
            except KeyError:
                return "<BAD_VARIABLE>"
        else:
            return super().get_value(key, args, kwargs)


def safe_format(text: str, *args, **kwargs) -> str:
    formatter = MessageFormatter()
    return formatter.format(text, *args, **kwargs)


def text_is_formattible(text: str) -> t.Union[str, bool]:
    try:
        return safe_format(text)
    except:
        return False


def list_of(items: list, sep: t.Optional[str] = "and") -> str:
    if len(items) > 2:
        return f"{', '.join(items[:-1])}, {sep} {items[-1]}"
    else:
        return f" {sep} ".join(items)


def ordinal(number: int) -> str:
    if str(number)[-2:] not in ("11", "12", "13"):
        return f"{number:,}{ORDINAL_ENDINGS.get(str(number)[-1], 'th')}"
    else:
        return f"{number:,}th"


def possessive(user: t.Union[Member, User]) -> str:
    name = getattr(user, "display_name", user.name)
    return f"{name}'{'s' if not name.endswith('s') else ''}"


async def binify(session: ClientSession, text: str, only_codeblocks=False) -> str:
    async def convert(body, to_replace, ext=""):
        async with session.post("https://mystb.in/documents", data=body) as response:
            if not 200 <= response.status <= 299:
                return response.status

            data = await response.json()
            return text.replace(to_replace, f"https://mystb.in/{data['key']}{ext}")

    if not only_codeblocks:
        return await convert(text, text)

    while (match := re.search(r"```([a-z]*)(\n?)([\s\S]*?)\n?```", text)) is not None:
        if not match.group(2):
            code = match.group(1) + match.group(3)
            ext = ""
        else:
            code = match.group(3) or match.group(1) or "None"
            ext = f".{match.group(1)}" or ""

        text = await convert(code, match.group(0), ext)
    return text
