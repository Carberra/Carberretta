from datetime import datetime

from discord import Embed

from carberretta.utils import DEFAULT_EMBED_COLOUR


def build_embed(**kwargs):
    ctx = kwargs.get("ctx")

    embed = Embed(
        title=kwargs.get("title"),
        description=kwargs.get("description"),
        colour=(
            kwargs.get("colour") or ctx.author.colour
            if ctx and ctx.author.colour.value
            else None or DEFAULT_EMBED_COLOUR
        ),
        timestamp=datetime.utcnow(),
    )
    embed.set_author(name=kwargs.get("header", "Carberretta"))
    embed.set_footer(
        text=kwargs.get("footer", f"Requested by {ctx.author.display_name}" if ctx else Embed.Empty),
        icon_url=ctx.author.avatar_url if ctx else Embed.Empty,
    )

    if thumbnail := kwargs.get("thumbnail"):
        embed.set_thumbnail(url=thumbnail)

    if image := kwargs.get("image"):
        embed.set_image(url=image)

    ### Above code in v1.4:
    # embed.set_thumbnail(url=kwargs.get("thumbnail", Embed.Empty))
    # embed.set_image(url=kwargs.get("image", Embed.Empty))

    for name, value, inline in kwargs.get("fields", []):
        embed.add_field(name=name, value=value, inline=inline)

    return embed
