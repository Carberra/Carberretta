"""
MOD

Handles automatic mod systems:
    Mention-spam preventer;
    Modmail system;
    Nicknames;
    Profanity filter.

**Manual moderation is handled by S4, and thus is not included.**
"""

import datetime as dt
import string
import typing as t
import json
import aiofiles
from collections import defaultdict
from content_filter import checkMessageList, useCustomListFile, updateListFromFile
from os import path

import discord
from discord.ext import commands

from carberretta import Config
from carberretta.utils import chron, DEFAULT_EMBED_COLOUR
from carberretta.utils.emoji import UNICODE_EMOJI
from carberretta.utils.errors import WordAlreadyAdded, WordNotFound


class Mod(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.modmail_cooldown: defaultdict = defaultdict(dt.datetime.utcnow)
        self.filter_file = f'{self.bot._dynamic}/filter.json'

        self.nickname_whitelist = set(
            string.ascii_letters
            + string.digits
            + string.punctuation.replace("@", " ")
            + "".join(UNICODE_EMOJI)
            + "áàȧâäǟǎăāãåǻǽǣćċĉčďḍḑḓéèėêëěĕēẽe̊ẹǵġĝǧğg̃ģĥḥíìiîïǐĭīĩịĵķǩĺļľŀḽm̂m̄ŉńn̂ṅn̈ňn̄ñņṋóòôȯȱöȫǒŏōõȭőọǿơp̄ŕřŗśŝṡšşṣťțṭṱúùûüǔŭūũűůụẃẁŵẅýỳŷÿȳỹźżžẓǯÁÀȦÂÄǞǍĂĀÃÅǺǼǢĆĊĈČĎḌḐḒÉÈĖÊËĚĔĒẼE̊ẸǴĠĜǦĞG̃ĢĤḤÍÌİÎÏǏĬĪĨỊĴĶǨĹĻĽĿḼM̂M̄ʼNŃN̂ṄN̈ŇN̄ÑŅṊÓÒȮȰÔÖȪǑŎŌÕȬŐỌǾƠP̄ŔŘŖŚŜṠŠȘṢŤȚṬṰÚÙÛÜǓŬŪŨŰŮỤẂẀŴẄÝỲŶŸȲỸŹŻŽẒǮæɑꞵðǝəɛɣıɩŋœɔꞷʊĸßʃþʋƿȝʒʔÆⱭꞴÐƎƏƐƔIƖŊŒƆꞶƱK’ẞƩÞƲǷȜƷʔąa̧ą̊ɓçđɗɖęȩə̧ɛ̧ƒǥɠħɦįi̧ɨɨ̧ƙłm̧ɲǫo̧øơɔ̧ɍşţŧųu̧ưʉy̨ƴĄA̧Ą̊ƁÇĐƊƉĘȨƏ̧Ɛ̧ƑǤƓĦꞪĮI̧ƗƗ̧ƘŁM̧ƝǪO̧ØƠƆ̧ɌŞŢŦŲU̧ƯɄY̨Ƴ"
        )

    async def modmail(self, message: discord.Message) -> None:
        if (retry_after := (self.modmail_cooldown[message.author.id] - dt.datetime.utcnow()).total_seconds()) > 0:
            return await message.channel.send(
                f"You're still on cooldown. Try again in {chron.long_delta(dt.timedelta(seconds=retry_after))}."
            )

        if not 50 <= len(message.content) <= 1000:
            return await message.channel.send("Your message should be between 50 and 1,000 characters long.")

        member = self.bot.guild.get_member(message.author.id)

        await self.modmail_channel.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "Modmail",
                    "color": member.colour.value,
                    "thumbnail": {"url": f"{member.avatar_url}"},
                    "footer": {"text": f"ID: {message.id}"},
                    "image": {"url": att[0].url if len((att := message.attachments)) else None},
                    "fields": [
                        {"name": "Member", "value": member.mention, "inline": False},
                        {"name": "Message", "value": message.content, "inline": False},
                    ],
                }
            )
        )
        await message.channel.send(
            "Message sent. If needed, a moderator will DM you regarding this issue. You'll need to wait 1 hour before sending another modmail."
        )
        self.modmail_cooldown[message.author.id] = dt.datetime.utcnow() + dt.timedelta(seconds=3600)

    async def unhoist(self, nickname: str) -> str:
        while nickname and nickname[0] not in string.ascii_letters:
            nickname = nickname[1:] if nickname[1:] else ""

        return " ".join(nickname.split(" "))

    async def nickname_valid(self, nickname: str) -> bool:
        return (
            set(nickname.replace(".", "", 1).replace(" ", "", 1)[:3]).issubset(set(string.ascii_letters))
            if nickname
            else False
        )

    async def profanity_filter(self, message: discord.Message) -> None:
        ctx = await self.bot.get_context(message, cls=commands.Context)

        if ctx.command is None:
            filter_result_raw = checkMessageList(message.content)
            filter_result = {
                'found': [],
                'censored': [],
                'count': []
            } # type: dict

            if filter_result_raw:
                await message.delete()

                for word in filter_result_raw:
                    filter_result['found'].append(word['word'] + '\n')
                    filter_result['censored'].append(word['censored'] + '\n')
                    filter_result['count'].append(str(word['count']) + '\n')

                warning_msg = await message.channel.send(f"{message.author.mention} please do not use offensive language!")

                member = self.bot.guild.get_member(message.author.id)

                await self.modlog_channel.send(
                    embed=discord.Embed.from_dict(
                        {
                            "title": "Filtered Message",
                            "color": 0xe33838,
                            "thumbnail": {"url": f"{member.avatar_url}"},
                            "footer": {"text": f"ID: {message.id}"},
                            "image": {"url": att[0].url if len((att := message.attachments)) else None},
                            "fields": [
                                {"name": "Member", "value": member.mention, "inline": False},
                                {"name": "Message", "value": message.content, "inline": False},
                                {"name": "Found", "value": '||' +
                                    "".join(filter_result['found']) + '||', "inline": True},
                                {"name": "Censored",
                                    "value": "".join(filter_result['censored']), "inline": True},
                                {"name": "Count",
                                    "value": "".join(filter_result['count']), "inline": True},
                                {"name": "Context",
                                    "value": f'[Jump to Message](https://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{warning_msg.id})', "inline": False},
                            ],
                        }
                    )
                )

        else:
            return

    async def load_filter_file(self):
        if path.isfile(self.filter_file):
            indexes_to_remove = []

            async def fix_category_type(item, checkType, replacement):
                try:
                    if not isinstance(filter_data[item], checkType):
                        filter_data[item] = replacement
                except:
                    filter_data[item] = replacement

            async def fix_item_type(item, item_name, checkType, section='mainFilter'):
                try:
                    if not isinstance(item[item_name], checkType):
                        return True
                except:
                    return True
                return False

            async def fix_item_null(index, item, item_name, replacement, section='mainFilter'):
                try:
                    if not item[item_name]:
                        filter_data[section][index][item_name] = replacement
                except:
                    filter_data[section][index][item_name] = replacement

            try:
                async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
                    filter_data = json.loads(await f.read())
            except:
                filter_data = {}

            if not isinstance(filter_data, dict):
                filter_data = {}

            await fix_category_type('mainFilter', list, [])
            await fix_category_type('dontFilter', None, None)
            await fix_category_type('conditionFilter', list, [])

            for index, item in enumerate(filter_data['mainFilter']):
                if not isinstance(item, dict):
                    indexes_to_remove.append(index)

                else:
                    try:
                        if not item['find'] or not item['word'] or not item['censored']:
                            indexes_to_remove.append(index)
                    except:
                        indexes_to_remove.append(index)
                    else:
                        indexes_to_remove.append(index) if await fix_item_type(item, 'find', str) else None
                        indexes_to_remove.append(index) if await fix_item_type(item, 'word', str) else None
                        indexes_to_remove.append(index) if await fix_item_type(item, 'censored', str) else None

                        await fix_item_null(index, item, 'added_by', self.bot.user.id)
                        await fix_item_null(index, item, 'added_on', dt.datetime.utcnow())
                        await fix_item_null(index, item, 'edited_by', None)
                        await fix_item_null(index, item, 'edited_on', None)

            for index in indexes_to_remove:
                filter_data['mainFilter'].pop(index)

            async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(filter_data, indent=4, cls=chron.DateTimeEncoder))

        else:
            filter_file_template = {
                "mainFilter": [],
                "dontFilter": None,
                "conditionFilter": []
            }

            async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(filter_file_template, indent=4, cls=chron.DateTimeEncoder))

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.modmail_channel = self.bot.get_channel(Config.MODMAIL_ID)
            self.modlog_channel = self.bot.get_channel(Config.MODLOG_ID)

            await self.load_filter_file()
            useCustomListFile(self.filter_file, path.abspath('./carberretta'))

            self.bot.ready.up(self)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if not message.author.bot:
            if isinstance(message.channel, discord.DMChannel):
                await self.modmail(message)
            elif isinstance(message.channel, discord.TextChannel):
                await self.profanity_filter(message)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        if not after.bot and after.nick and before.nick != after.nick:
            try:
                nickname = await self.unhoist("".join(c for c in after.nick if c in self.nickname_whitelist))

                if await self.nickname_valid(nickname):
                    if nickname != after.nick:
                        await after.edit(nick=nickname, reason="Nickname contains invalid characters")
                else:
                    await after.edit(
                        nick=before.nick if await self.nickname_valid(before.nick) else None, reason="Invalid nickname"
                    )
            except discord.Forbidden:
                pass

    @commands.command(name="validatenicknames", aliases=["va"])
    @commands.has_permissions(manage_nicknames=True)
    async def validatenicknames_command(self, ctx):
        for member in ctx.guild.members:
            if not member.bot and member.nick:
                try:
                    nickname = await self.unhoist("".join(c for c in member.nick if c in self.nickname_whitelist))

                    if await self.nickname_valid(nickname):
                        if nickname != member.nick:
                            await member.edit(nick=nickname, reason="Nickname contains invalid characters")
                    else:
                        await member.edit(nick=None, reason="Invalid nickname")
                except discord.Forbidden:
                    pass
        await ctx.send("Done.")

    @commands.group(name="filter", aliases=["f"], invoke_without_command=True)
    # @commands.has_permissions(manage_guild=True)
    async def filter(self, ctx) -> None:
        await ctx.send("+filter <action> [input]...")

    @filter.command(name="add")
    # @commands.has_permissions(manage_guild=True)
    async def filter_add_command(self, ctx, find: str, word: str, censored: str) -> None:
        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = find.replace('+', 't').replace('!', 'i').replace('@', 'a').replace('1', 'i').replace('0', 'o').replace('3', 'e').replace('$', 's').replace('*', '#')

        for word_found in filter_data['mainFilter']:
            if word_found['find'] == find_modified:
                raise WordAlreadyAdded(find)

        word_to_add = {
            'find': find_modified,
            'word': word,
            'censored': censored,
            'added_by': ctx.author.id,
            'added_on': dt.datetime.utcnow(),
            'edited_by': None,
            'edited_on': None
        }

        filter_data['mainFilter'].append(word_to_add)

        async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(filter_data, indent=4, cls=chron.DateTimeEncoder))

        updateListFromFile()

        await ctx.send(f'Word `{find}` added into the filter.')

    @filter.command(name="remove")
    # @commands.has_permissions(manage_guild=True)
    async def filter_remove_command(self, ctx, find: str) -> None:
        found_word_in_filter = False

        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = find.replace('+', 't').replace('!', 'i').replace('@', 'a').replace('1', 'i').replace('0', 'o').replace('3', 'e').replace('$', 's').replace('*', '#')

        for word_found in filter_data['mainFilter']:
            if word_found['find'] == find_modified:
                found_word_in_filter = True
                word_found_info = word_found

        if not found_word_in_filter:
            raise WordNotFound(find)

        word_to_remove = {
            'find': find_modified,
            'word': word_found_info['word'],
            'censored': word_found_info['censored'],
            'added_by': word_found_info['added_by'],
            'added_on': word_found_info['added_on'],
            'edited_by': word_found_info['edited_by'],
            'edited_on': word_found_info['edited_on']
        }

        filter_data['mainFilter'].remove(word_to_remove)

        async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(filter_data, indent=4, cls=chron.DateTimeEncoder))

        updateListFromFile()

        await ctx.send(f'Word `{find}` removed from the filter.')

    @filter.command(name="edit")
    # @commands.has_permissions(manage_guild=True)
    async def filter_edit_command(self, ctx, find: str, new_find: str, new_word: str, new_censored: str) -> None:
        found_word_in_filter = False

        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = find.replace('+', 't').replace('!', 'i').replace('@', 'a').replace('1', 'i').replace('0', 'o').replace('3', 'e').replace('$', 's').replace('*', '#')
        new_find_modified = new_find.replace('+', 't').replace('!', 'i').replace('@', 'a').replace('1', 'i').replace('0', 'o').replace('3', 'e').replace('$', 's').replace('*', '#')

        for index, word_found in enumerate(filter_data['mainFilter']):
            if word_found['find'] == find_modified:
                found_word_in_filter = True
                word_found_index = index
                word_found_info = word_found

            elif word_found['find'] == new_find_modified:
                raise WordAlreadyAdded(new_word)

        if not found_word_in_filter:
            raise WordNotFound(find)

        word_to_edit = {
            'find': new_find_modified,
            'word': new_word,
            'censored': new_censored,
            'added_by': word_found_info['added_by'],
            'added_on': word_found_info['added_on'],
            'edited_by': ctx.author.id,
            'edited_on': dt.datetime.utcnow()
        }

        filter_data['mainFilter'][word_found_index] = word_to_edit

        async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(filter_data, indent=4, cls=chron.DateTimeEncoder))

        updateListFromFile()

        await ctx.send(f'Word `{find}` modified to be `{new_find}`.')

    @filter.command(name="list")
    # @commands.has_permissions(manage_guild=True)
    async def filter_list_command(self, ctx, find: str = 'all') -> None:
        found_word_in_filter = False
        list_embed_fields = []

        list_output = {
            'find': [],
            'word': [],
            'censored': []
        } # type: dict

        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = find.replace('+', 't').replace('!', 'i').replace('@', 'a').replace('1', 'i').replace('0', 'o').replace('3', 'e').replace('$', 's').replace('*', '#')

        if find != 'all':
            for index, word_found in enumerate(filter_data['mainFilter']):
                if word_found['find'] == find_modified:
                    found_word_in_filter = True
                    word_found_index = index

                    result_text = f'Result: #{index + 1}'
                    list_embed_fields = [
                        {
                            "name": "Find",
                            "value": '||' + word_found['find'] + '||',
                            "inline": True,
                        },
                        {
                            "name": "Word",
                            "value": '||' + word_found['word'] + '||',
                            "inline": True,
                        },
                        {
                            "name": "Censored",
                            "value": word_found['censored'],
                            "inline": True,
                        },
                        {
                            "name": "Added By",
                            "value": self.bot.guild.get_member(word_found['added_by']).mention ,
                            "inline": True,
                        },
                        {
                            "name": "Added On",
                            "value": chron.short_date_and_time(chron.from_iso(word_found['added_on'])),
                            "inline": True,
                        },
                        {
                            "name": "Last Edited By",
                            "value": self.bot.guild.get_member(word_found['edited_by']).mention if word_found['edited_by'] else "Not Edited",
                            "inline": True,
                        },
                        {
                            "name": "Last Edited On",
                            "value": chron.short_date_and_time(chron.from_iso(word_found['edited_on'])) if word_found['edited_on'] else "Not Edited",
                            "inline": True,
                        }
                    ]

        else:
            for word_found in filter_data['mainFilter']:
                list_output['find'].append(word_found['find'] + '\n')
                list_output['word'].append(word_found['word'] + '\n')
                list_output['censored'].append(word_found['censored'] + '\n')

            found_word_in_filter = True
            result_text = 'Results: ' + str(len(list_output['find']))
            list_embed_fields = [
                {
                    "name": "Find",
                    "value": '||' + "".join(list_output['find']) + '||',
                    "inline": True
                },
                {
                    "name": "Word",
                    "value": '||' + "".join(list_output['word']) + '||',
                    "inline": True
                },
                {
                    "name": "Censored",
                    "value": "".join(list_output['censored']),
                    "inline": True
                }
            ]


        if not found_word_in_filter:
            raise WordNotFound(find)

        await ctx.send(
            embed=discord.Embed.from_dict(
                {
                    "title": "Filter List",
                    "color": DEFAULT_EMBED_COLOUR,
                    "author": {"name": "Information"},
                    "footer": {
                        "text": f"Requested by {ctx.author.display_name} | {result_text}",
                        "icon_url": f"{ctx.author.avatar_url}",
                    },
                    "fields": list_embed_fields
                }
            )
        )




def setup(bot: commands.Bot) -> None:
    bot.add_cog(Mod(bot))
