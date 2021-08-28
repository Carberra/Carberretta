"""
!!! DON'T USE THIS IN YOUR OWN BOTS !!!

This is coded like shit in a rush, so don't use it. V2 will have a
better one (:
"""

import datetime as dt
import json
import os
import typing as t

import aiofiles
import discord
from discord.ext import commands

from carberretta import Config


class Role2(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.react_path = f"{self.bot._dynamic}/rr.json"
        self.reacts = {}

    async def load_reacts(self) -> t.Mapping[str, int]:
        if os.path.isfile(self.react_path):
            async with aiofiles.open(self.react_path, encoding="utf-8") as f:
                data = json.loads(await f.read())
            return data
        else:
            return {}

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.reacts = await self.load_reacts()
            self.bot.ready.up(self)

    @commands.group(name="rolereact", aliases=["rr"])
    @commands.has_permissions(administrator=True)
    async def rr(self, ctx) -> None:
        await ctx.send("+rr create <stack> <channel> <colour> <message> <selection>")

    @rr.command(name="create")
    @commands.has_permissions(administrator=True)
    async def command_create(
        self, ctx, stack: bool, channel: discord.TextChannel, colour: str, message: str, *, selection: str
    ) -> None:
        roles = []
        for i in (j := iter(selection.split(" "))) :
            roles.append((i, discord.utils.get(ctx.guild.roles, mention=next(j))))

        embed = discord.Embed.from_dict(
            {
                "title": message,
                "description": "\n".join([f"{emoji}: {role.name}" for emoji, role in roles]),
                "color": int(colour, base=16),
                "author": {"name": "Role Reaction"},
                "footer": {
                    "text": (
                        "You are limited to one role.",
                        "You can give yourself as many roles as you like."
                    )[stack] + (
                        "\nThis won't work if the ten minute "
                        "verification timer is still ticking."
                    )
                },
            }
        )
        message = await channel.send(embed=embed)
        for emoji, _ in roles:
            await message.add_reaction(emoji)

        self.reacts.update({
            f"{message.id}": {
                "stack": stack,
                "roles": {
                    emoji: role.id
                    for emoji, role in roles
                }
            }
        })

        async with aiofiles.open(self.react_path, "w", encoding="utf-8") as f:
            await f.write(json.dumps(self.reacts, ensure_ascii=False))

        await ctx.send("Done.")

    @rr.command(name="edit")
    @commands.has_permissions(administrator=True)
    async def command_edit(self, ctx) -> None:
        ...

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        if f"{payload.message_id}" not in self.reacts.keys() or payload.member.bot:
            return

        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        data = self.reacts[f"{message.id}"]
        for reaction in message.reactions:
            emoji = getattr(reaction.emoji, "name", reaction.emoji)

            if emoji not in data["roles"].keys():
                continue

            reactors = await reaction.users().flatten()

            if payload.member in reactors:
                role = message.guild.get_role(data["roles"][emoji])

                if role in payload.member.roles:
                    await payload.member.remove_roles(message.guild.get_role(data["roles"][emoji]))
                else:
                    if not data["stack"]:
                        await payload.member.remove_roles(
                            *(message.guild.get_role(i) for i in data["roles"].values()),
                            atomic=False,
                        )
                    await payload.member.add_roles(message.guild.get_role(data["roles"][emoji]))

                await reaction.remove(payload.member)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload) -> None:
        ...


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Role2(bot))
