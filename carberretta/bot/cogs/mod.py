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


class Mod(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def modmail(self, message: discord.Message) -> None:
        if not 50 <= len(message.content) <= 1000:
            await message.channel.send("Your message should be between 50 and 1,000 characters long.")

        else:
            member = self.bot.guild.get_member(message.author.id)

            await self.modmail_channel.send(embed=discord.Embed.from_dict({
                "title": "Modmail",
                "colour": member.colour,
                "thumbnail": { "url": f"{member.avatar_url}" },
                "footer": { "text": f"ID: {message.id}" },
                "image": { "url": att[0].url if len((att := message.attachments)) else None },
                "fields": [
                    { "name": "Member", "value": member.mention, "inline": False },
                    { "name": "Message", "value": message.content, "inline": False }
                ]
            }))
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
