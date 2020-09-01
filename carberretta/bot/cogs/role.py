"""
ROLE

Handles role based operations:
    Colour reactions;
    Opt-in and -out commands.
"""


import typing as t

import discord
from discord.ext import commands

from carberretta import Config


class Role(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

        self._cache: t.Dict = {}

    @commands.group(name="rolereact", aliases=["rr"])
    async def rr(self, ctx) -> None:
        pass

    @rr.command(name="create")
    async def command_create(
        self, ctx, stack: bool, channel: discord.TextChannel, message: str, *, selection: str
    ) -> None:
        roles = []
        for i in (j := iter(selection.split(" "))) :
            roles.append((i, discord.utils.get(ctx.guild.roles, mention=next(j))))

        pretty_roles = "\n".join([f"{emoji}: {role.name}" for emoji, role in roles])
        embed = discord.Embed(title="Role Reaction", description=f"{message}\n{pretty_roles}")

        self._cache.update(
            {
                discord.utils.get(self.bot.cached_messages, id=(await channel.send(embed=embed)).id): {
                    "roles": {emoji: role for emoji, role in roles},
                    "stack": stack,
                }
            }
        )

    @rr.command(name="edit")
    async def command_edit(self, ctx) -> None:
        pass

    @rr.command(name="cache")
    async def command_cache(self, ctx) -> None:
        await ctx.send(f"{self._cache}")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload) -> None:
        if not payload.member.bot:
            if message := next((m for m in self._cache if m.id == payload.message_id), None):
                data = self._cache[message]
                try:
                    if not data["stack"]:
                        for emoji in (
                            reaction.emoji for reaction in message.reactions if reaction.emoji != payload.emoji.name
                        ):
                            try:
                                await message.remove_reaction(emoji, payload.member)
                            except:
                                raise
                        await payload.member.remove_roles(
                            *data["roles"].values(),
                            reason=f"Removed due to role reaction to message {payload.message_id}",
                        )

                    await payload.member.add_roles(
                        data["roles"].get(f"{payload.emoji}"),
                        reason=f"Added due to role reaction to message {payload.message_id}",
                    )
                except:
                    print(f"{payload.emoji} not in {data['roles']=}")
                    raise

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload) -> None:
        if roles := next((self._cache[m]["roles"] for m in self._cache if m.id == payload.message_id), None):
            if not (member := self.bot.get_guild(payload.guild_id).get_member(payload.user_id)).bot:
                try:
                    await self.bot.get_guild(payload.guild_id).get_member(payload.user_id).remove_roles(
                        roles.get(f"{payload.emoji}"),
                        reason=f"Removed due to role reaction to message {payload.message_id}",
                    )
                except:
                    print(f"{payload.emoji} not in {roles=}")


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Role(bot))
