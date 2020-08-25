"""
MOD

Handles automatic mod systems:
    Profanity filter;
    Mention-spam preventer;
    Modmail system.

**Manual moderation is handled by S4, and thus is not included.**
"""


import discord
from discord.ext import commands

from carberretta import Config
from carberretta.utils.embed import build_embed


class Mod(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def modmail(self, message: discord.Message) -> None:
        if not 50 <= len(message.content) <= 1000:
            await message.channel.send("Your message should be between 50 and 1,000 characters long.")

        else:
            member = self.bot.guild.get_member(message.author.id)

            fields = (
                ("Member", member.mention, False),
                ("Message", message.content, False),
            )

            embed = build_embed(
                title="Modmail",
                colour=member.colour,
                thumbnail=member.avatar_url,
                footer=f"ID: {message.id}",
                image=att[0].url if len((att := message.attachments)) else None,
                fields=fields,
            )

            await self.modmail_channel.send(embed=embed)
            await message.channel.send("Message sent. If needed, a moderator will DM you regarding this issue.")

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.modmail_channel = self.bot.get_channel(Config.MODMAIL_ID)
            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.author.bot:
            if isinstance(message.channel, discord.DMChannel):
                await self.modmail(message)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Mod(bot))
