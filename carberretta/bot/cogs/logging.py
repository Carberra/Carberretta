"""
LOGGING

Handles logging of guild events:
    Nickname Add
    Nickname Remove
    Nickname Change

    Message Delete
    Message Edit
    Bulk Message Delete

    Role Add
    Role Remove

    Member Join
    Member Leave
"""
from datetime import datetime
from datetime import timedelta
from typing import List
import mystbin # pip install mystbin.py

import discord
from discord.ext import commands

from carberretta.utils import DEFAULT_EMBED_COLOUR

mystbin_client = mystbin.Client()


class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.log_channel = 762427685556191283
        self.min_days = 7


    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        channel = self.bot.get_channel(self.log_channel)

        if before.nick != after.nick:
            if before.nick is None:
                embed = discord.Embed(
                    title="Nickname Added",
                    color=DEFAULT_EMBED_COLOUR,
                    timestamp=datetime.utcnow()
                )
                embed.description = f"User: {after.mention}\nNickname: {after.nick}"
                embed.set_author(name=after, icon_url=after.avatar_url)
                embed.set_footer(text=f"{after.name} | ID: {after.id}")
                embed.set_thumbnail(url=after.avatar_url)
                await channel.send(embed=embed)
            elif after.nick is None:
                embed = discord.Embed(
                    title="Nickname Reset",
                    color=DEFAULT_EMBED_COLOUR,
                    timestamp=datetime.utcnow()
                )
                embed.description = f"User: {after.mention}\nFrom: {before.nick}"
                embed.set_author(name=after, icon_url=after.avatar_url)
                embed.set_footer(text=f"{after.name} | ID: {after.id}")
                embed.set_thumbnail(url=after.avatar_url)
                await channel.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Nickname Changed",
                    color=DEFAULT_EMBED_COLOUR,
                    timestamp=datetime.utcnow()
                )
                embed.description = f"User: {after.mention}\n\nFrom: {before.nick}\nTo: {after.nick}"
                embed.set_author(name=after, icon_url=after.avatar_url)
                embed.set_footer(text=f"{after.name} | ID: {after.id}")
                embed.set_thumbnail(url=after.avatar_url)
                await channel.send(embed=embed)

        elif before.roles != after.roles:
            new = [roles for roles in after.roles if roles not in before.roles]
            old = [roles for roles in before.roles if roles not in after.roles]

            if len(after.roles) >= 15:
                rest = len(after.roles) - 15
                roles = " | ".join(role.mention for role in list(reversed(after.roles[:rest])))
                sentence = f"{roles} and **{rest}** more"

            else:
                sentence = " | ".join(role.mention for role in list(reversed(after.roles)))

            if len(new) >= 1:
                new_format = " | ".join(role.mention for role in new)
                embed = discord.Embed(
                    title="Role Added",
                    color=DEFAULT_EMBED_COLOUR,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"{after.name} | ID: {after.id}")
                embed.set_author(name=after, icon_url=after.avatar_url)
                embed.description = f"User: {after.mention}\n\nAdded:\n{new_format}\n\nRoles:\n{sentence}"

            if len(old) >= 1:
                old_format = " | ".join(role.mention for role in old)
                embed = discord.Embed(
                    title="Role Removed",
                    color=DEFAULT_EMBED_COLOUR,
                    timestamp=datetime.utcnow()
                )
                embed.set_footer(text=f"{after.name} | ID: {after.id}")
                embed.set_author(name=after, icon_url=after.avatar_url)
                embed.description = f"User: {after.mention}\n\nRemoved Role:\n{old_format}\n\nRoles:\n{sentence}"

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        channel = self.bot.get_channel(self.log_channel)

        if before.name != after.name:
            embed = discord.Embed(
                title="Username Changed",
                color=DEFAULT_EMBED_COLOUR,
                timestamp=datetime.utcnow()
            )
            embed.description = f"User: {after.mention}\n\nFrom: {before.name}\nTo: {after.name}"
            embed.set_author(name=after, icon_url=after.avatar_url)
            embed.set_footer(text=f"{after.name} | ID: {after.id}")
            embed.set_thumbnail(url=after.avatar_url)
            await channel.send(embed=embed)

        elif before.avatar_url != after.avatar_url:
            embed = discord.Embed(
                title="Avatar Changed",
                color=DEFAULT_EMBED_COLOUR,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"{after.name} | ID: {after.id}")
            embed.set_author(name=after, icon_url=after.avatar_url)

            embed.set_thumbnail(url=before.avatar_url)
            embed.set_image(url=after.avatar_url)
            embed.description = f"User: {after.mention}\nOld Avatar: Thumbnail\nNew Avatar: Image"

            await channel.send(embed=embed)

        elif before.discriminator != after.discriminator:
            embed = discord.Embed(
                title="Discriminator Changed",
                color=DEFAULT_EMBED_COLOUR,
                timestamp=datetime.utcnow()
            )
            embed.set_footer(text=f"{after.name} | ID: {after.id}")
            embed.set_author(name=after, icon_url=after.avatar_url)
            embed.set_thumbnail(url=before.avatar_url)
            embed.description = f"User: {after.mention}\nOld Discriminator: {before.discriminator}\nNew Discriminator: {after.discriminator}"

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        channel = self.bot.get_channel(self.log_channel)

        if not message.author.bot:
            time = datetime.utcnow() - timedelta(seconds=3)
            async for entry in message.guild.audit_logs(limit=1, oldest_first=False, after=time, action=discord.AuditLogAction.message_delete):
                executer = entry.user
            else:
                executer = None

            if len(message.content) <= 1024:
                fields = [("Message Content", message.content or "View Attachment", False)]
            else:
                fields = [("Message Content #1", message.content[:1000], False),
                          ("Message Content #2", message.content[1000:], False)]

            embed = discord.Embed(title="Message Deleted",
                                  color=DEFAULT_EMBED_COLOUR,
                                  timestamp=datetime.utcnow())
            if executer:
                embed.description = f"Executed by: {executer.mention}\nChannel: {message.channel.mention} | {message.channel}\nAuthor: {message.author.mention}"
            else:
                embed.description = f"Executed by: Author\nChannel: {message.channel.mention} | {message.channel}\nAuthor: {message.author.mention}"

            if message.attachments:
                attach_string = "".join(f"[Link]({attach.proxy_url})" for attach in message.attachments)
                fields += [("Attachment Link(s)", attach_string, False)]

            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

            if executer:
                embed.set_footer(text=f"{executer.name} | ID: {executer.id}")
            else:
                embed.set_footer(text=f"{message.author.name} | ID: {message.author.id}")
            embed.set_author(name=message.author, icon_url=message.author.avatar_url)

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        channel = self.bot.get_channel(self.log_channel)

        if before.content != after.content and not after.author.bot:
            def create_edit_field(status: str) -> None:
                if status == "before":
                    if len(before.content) <= 1024:
                        fields = [(f"Before Content", before.content or "View Attachment", False)]
                    else:
                        fields = [(f"Before Content #1", before.content[:1000], False),
                                (f"Before Content #2", before.content[1000:], False)]

                    if before.attachments:
                        attach_string = "".join(f"[Link]({attach.proxy_url})" for attach in before.attachments)
                        fields += [("Before Attachment Link(s)", attach_string, False)]
                else:
                    if len(after.content) <= 1024:
                        fields = [(f"After Content", after.content or "View Attachment", False)]
                    else:
                        fields = [(f"After Content #1", after.content[:1000], False),
                                (f"After Content #2", after.content[1000:], False)]

                    if after.attachments:
                        attach_string = "".join(f"[Link]({attach.proxy_url})" for attach in after.attachments)
                        fields += [("After Attachment Link(s)", attach_string, False)]

                for name, value, inline in fields:
                    embed.add_field(name=name, value=value, inline=inline)

            embed = discord.Embed(title="Message Edited",
                                    color=DEFAULT_EMBED_COLOUR,
                                    timestamp=datetime.utcnow())
            embed.description = f"Author: {after.author.mention}\n\nChannel: {after.channel.mention} | {after.channel}\nMessage: [Jump To Message]({after.jump_url})\nMessage ID: {after.id}"
            create_edit_field("before")
            create_edit_field("after")
            embed.set_footer(text=f"{after.author.name} | ID: {after.author.id}")
            embed.set_author(name=after.author, icon_url=after.author.avatar_url)

            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: List[discord.Member]) -> None:
        try:
            channel = self.bot.get_channel(self.log_channel)
            guild = self.bot.get_guild(messages[0].guild.id)

            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.message_bulk_delete):
                executer = entry.user

            content = ""

            for message in messages:
                msg_content = f"CONTENT: {message.content}\n" if content != " " else ""
                msg_embed = ""
                if message.embeds:
                    for embed in message.embeds:
                        msg_embed += f"EMBED:\n{f'Title: {embed.title}' or 'No Title'}\n{f'Description: {str(embed.description)}' or 'No Description'}\n{f'Color: {embed.color}' or 'No Color'}\n{f'Footer: {embed.footer.text}' or 'No Footer'}\n{f'Author: {embed.author.name}' or 'No Footer'}"
                content += f"[{message.created_at.strftime('%d %b %Y %H:%M')}] {message.author}: {msg_content}{msg_embed}\n\n"

            paste = await mystbin_client.post(content, syntax="css")
            url = str(paste)

            embed = discord.Embed(
                title="Bulk Message Deletion",
                colour=DEFAULT_EMBED_COLOUR,
                timestamp=datetime.utcnow())
            embed.description = f"Executed by: {executer.mention}\nChannel: {messages[0].channel.mention}\nMessage Count: {len(messages)}\nDeleted Messages: {url}"
            embed.set_footer(text=f"{executer.name} | ID: {executer.id}")
            embed.set_author(name=executer, icon_url=executer.avatar_url)

            await channel.send(embed=embed)
        except Exception as e:
            print(e)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        channel = self.bot.get_channel(self.log_channel)

        days = (datetime.utcnow() - member.created_at).days
        if days <= self.min_days:
            warn = f":warning: This account was created less than {self.min_days} days ago\n"
        else:
            warn = ""

        embed = discord.Embed(
            title="Member Join",
            colour=DEFAULT_EMBED_COLOUR,
            timestamp=datetime.utcnow())
        embed.description = f"{warn}User: {member.mention}\nAccount Created On: {member.created_at.strftime('%d %b %Y %H:%M')} ({days} days ago)"
        embed.set_footer(text=f"{member.name} | ID: {member.id}")
        embed.set_author(name=member, icon_url=member.avatar_url)

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        channel = self.bot.get_channel(self.log_channel)

        days = (datetime.utcnow() - member.created_at).days
        embed = discord.Embed(
            title="Member Leave",
            colour=DEFAULT_EMBED_COLOUR,
            timestamp=datetime.utcnow())
        embed.description = f"User: {member}\nAccount Created On: {member.created_at.strftime('%d %b %Y %H:%M')} ({days} days ago)"
        embed.set_footer(text=f"{member.name} | ID: {member.id}")
        embed.set_author(name=member, icon_url=member.avatar_url)

        await channel.send(embed=embed)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Logging(bot))
