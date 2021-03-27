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
import json
import string
import typing as t
from collections import defaultdict
from pathlib import Path

import aiofiles
import discord
from content_filter import Filter
from discord.ext import commands

from carberretta import Config
from carberretta.utils import DEFAULT_EMBED_COLOUR, chron
from carberretta.utils.emoji import UNICODE_EMOJI
from carberretta.utils.errors import WordAlreadyAdded, WordNotFound, InvalidAction
from carberretta.utils.menu import MultiPageMenu


class FilterListMenu(MultiPageMenu):
    def __init__(self, ctx, pagemaps):
        super().__init__(ctx, pagemaps, timeout=120.0)


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
                    "image": {"url": att[0].url if (att := message.attachments) else None},
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
            filter_result_raw = self.filter.check(message.content).as_list
            filter_result = {
                'raw': [],
                'found': [],
                'count': []
            } # type: dict

            if filter_result_raw:
                actions = []

                async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
                    filter_data = json.loads(await f.read())

                for word in filter_result_raw:
                    filter_result['raw'].append(word['find'] + '\n')
                    filter_result['found'].append(word['word'] + '\n')
                    filter_result['count'].append(str(word['count']) + '\n')

                    for filter_word in filter_data[word['filter']]:
                        if filter_word['find'] == word['find']:
                            actions.append(filter_word['action'])

                if "ban" in actions:
                    action = "ban"
                    warning_msg = await message.channel.send(f"{message.author.mention}, please do not use offensive language.")
                elif "kick" in actions:
                    action = "kick"
                    warning_msg = await message.channel.send(f"{message.author.mention}, please do not use offensive language.")
                elif "warn" in actions:
                    action = "warn"
                    warning_msg = await message.channel.send(f"{message.author.mention}, please do not use offensive language.")

                member = self.bot.guild.get_member(message.author.id)

                await self.modlog_channel.send(
                    embed=discord.Embed.from_dict(
                        {
                            "title": "Filtered Message",
                            "color": 0xe33838,
                            "thumbnail": {"url": f"{member.avatar_url}"},
                            "footer": {"text": f"Message ID: {message.id}"},
                            "image": {"url": att[0].url if (att := message.attachments) else None},
                            "fields": [
                                {"name": "Member", "value": member.mention, "inline": False},
                                {"name": "Message", "value": message.content, "inline": False},
                                {"name": "Identified", "value": '||' + "".join(filter_result['raw']) + '||', "inline": True},
                                {"name": "Found", "value": '||' + "".join(filter_result['found']) + '||', "inline": True},
                                {"name": "Count", "value": "".join(filter_result['count']), "inline": True},
                                {"name": "Context", "value": f'[Jump to Message]({warning_msg.jump_url})', "inline": True},
                                {"name": "Action", "value": f'{action.capitalize()}', "inline": True},
                            ],
                        }
                    )
                )

                await message.delete()

        else:
            return

    async def to_filter_format(self, text: str):
        conversion_table = str.maketrans({
            '"': None,
            ',': None,
            '.': None,
            '-': None,
            '\'': None,
            '+': 't',
            '!': 'i',
            '@': 'a',
            '1': 'i',
            '0': 'o',
            '3': 'e',
            '$': 's',
            '*': '#',
        })

        return text.translate(conversion_table)

    async def from_filter_format(self, text: str):
        return text.replace('#', '*')

    async def word_found(self, filter_data: dict, filter_type: str, find: str, already_added = False, not_found = False):
        found_word_in_filter = False

        for idx, word_found in enumerate(filter_data[filter_type]):
            if word_found['find'] == find:
                found_word_in_filter = True
                index = idx
                info = word_found

                if already_added:
                    raise WordAlreadyAdded(find)

        if not found_word_in_filter and not_found:
            raise WordNotFound(find)

        try:
            return index, info
        except:
            return False

    async def action_type(self, action: str):
        action_types = ('warn', 'kick', 'ban')

        if action not in action_types:
            raise InvalidAction(action, action_types)

        return

    async def check_filter_file(self):
        if not Path(self.filter_file).is_file():
            filter_file_template = {
                "mainFilter": [],
                "dontFilter": None,
                "conditionFilter": []
            }

            async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
                await f.write(json.dumps(filter_file_template, cls=chron.DateTimeEncoder))

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready.booted:
            self.modmail_channel = self.bot.get_channel(Config.MODMAIL_ID)
            self.modlog_channel = self.bot.get_channel(Config.MODLOG_ID)

            await self.check_filter_file()
            self.filter = Filter(list_file=self.filter_file)

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
    @commands.has_role(Config.MODERATOR_ROLE_ID)
    async def filter(self, ctx) -> None:
        await ctx.send("+filter <action> [input]...")

    @filter.command(name="add")
    @commands.has_role(Config.MODERATOR_ROLE_ID)
    async def filter_add_command(self, ctx, find: str, word: str, action: str = "warn") -> None:
        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = await self.to_filter_format(find)
        await self.word_found(filter_data, 'mainFilter', find_modified, already_added=True)
        await self.word_found(filter_data, 'conditionFilter', find_modified, already_added=True)
        await self.action_type(action)

        word_to_add = {
            'find': find_modified,
            'word': word,
            'censored': word,
            'added_by': ctx.author.id,
            'added_on': dt.datetime.utcnow(),
            'edited_by': None,
            'edited_on': None,
            'action': action
        }

        filter_data['mainFilter'].append(word_to_add)

        async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(filter_data, cls=chron.DateTimeEncoder))

        self.filter.reload_file()

        await ctx.send(f'Word `{find}` added into the filter.')

    @filter.command(name="remove", aliases=["rm"])
    @commands.has_role(Config.MODERATOR_ROLE_ID)
    async def filter_remove_command(self, ctx, find: str) -> None:
        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = await self.to_filter_format(find)
        word_found_index, word_found_info = await self.word_found(filter_data, 'mainFilter', find_modified, not_found=True)

        word_to_remove = {
            'find': find_modified,
            'word': word_found_info['word'],
            'censored': word_found_info['censored'],
            'added_by': word_found_info['added_by'],
            'added_on': word_found_info['added_on'],
            'edited_by': word_found_info['edited_by'],
            'edited_on': word_found_info['edited_on'],
            'action': word_found_info['action']
        }

        filter_data['mainFilter'].remove(word_to_remove)

        async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(filter_data, cls=chron.DateTimeEncoder))

        self.filter.reload_file()

        await ctx.send(f'Word `{find}` removed from the filter.')

    @filter.command(name="edit")
    @commands.has_role(Config.MODERATOR_ROLE_ID)
    async def filter_edit_command(self, ctx, find: str, new_find: str, new_word: str, new_action: str = "warn") -> None:
        found_word_in_filter = False

        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = await self.to_filter_format(find)
        new_find_modified = await self.to_filter_format(new_find)

        for index, word_found in enumerate(filter_data['mainFilter']):
            if word_found['find'] == find_modified:
                found_word_in_filter = True
                word_found_index = index
                word_found_info = word_found

            elif word_found['find'] == new_find_modified:
                raise WordAlreadyAdded(new_find)

        for word_found in filter_data['conditionFilter']:
            if word_found['find'] == new_find_modified:
                raise WordAlreadyAdded(new_find)

        if not found_word_in_filter:
            raise WordNotFound(find)

        await self.action_type(new_action)

        word_to_edit = {
            'find': new_find_modified,
            'word': new_word,
            'censored': new_word,
            'added_by': word_found_info['added_by'],
            'added_on': word_found_info['added_on'],
            'edited_by': ctx.author.id,
            'edited_on': dt.datetime.utcnow(),
            'action': new_action
        }

        filter_data['mainFilter'][word_found_index] = word_to_edit

        async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(filter_data, cls=chron.DateTimeEncoder))

        self.filter.reload_file()

        await ctx.send(f'Word `{find}` modified to be `{new_find}`.')

    async def chunk_list(self, list_to_split, segment_len):
        return [list_to_split[i:i + segment_len] for i in range(0, len(list_to_split), segment_len)]

    @filter.command(name="conditionadd", aliases=["cadd"])
    @commands.has_role(Config.MODERATOR_ROLE_ID)
    async def filter_add_condition_command(self, ctx, find: str, word: str, space_before: str, action: str = "warn") -> None:
        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = await self.to_filter_format(find)

        if space_before == 'y' or space_before == 'yes' or space_before == 'true' or space_before == 't':
            require_space_translated = True
        elif space_before == 'n' or space_before == 'no' or space_before == 'false' or space_before == 'f':
            require_space_translated = False
        else:
            raise commands.BadArgument('Invalid answer to space_before. Be sure to define a yes or no answer.')

        await self.word_found(filter_data, 'mainFilter', find_modified, already_added=True)
        await self.word_found(filter_data, 'conditionFilter', find_modified, already_added=True)
        await self.action_type(action)

        word_to_add = {
            'find': find_modified,
            'word': word,
            'censored': word,
            'added_by': ctx.author.id,
            'added_on': dt.datetime.utcnow(),
            'edited_by': None,
            'edited_on': None,
            'require_space': require_space_translated,
            'action': action
        }

        filter_data['conditionFilter'].append(word_to_add)

        async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(filter_data, cls=chron.DateTimeEncoder))

        self.filter.reload_file()

        await ctx.send(f'Word `{find}` added into the condition filter.')

    @filter.command(name="conditionremove", aliases=["crm"])
    @commands.has_role(Config.MODERATOR_ROLE_ID)
    async def filter_remove_condition_command(self, ctx, find: str) -> None:
        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = await self.to_filter_format(find)
        word_found_index, word_found_info = await self.word_found(filter_data, 'conditionFilter', find_modified, not_found=True)

        word_to_remove = {
            'find': find_modified,
            'word': word_found_info['word'],
            'censored': word_found_info['censored'],
            'added_by': word_found_info['added_by'],
            'added_on': word_found_info['added_on'],
            'edited_by': word_found_info['edited_by'],
            'edited_on': word_found_info['edited_on'],
            'require_space': word_found_info['require_space'],
            'action': word_found_info['action']
        }

        filter_data['conditionFilter'].remove(word_to_remove)

        async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(filter_data, cls=chron.DateTimeEncoder))

        self.filter.reload_file()

        await ctx.send(f'Word `{find}` removed from the condition filter.')

    @filter.command(name="conditionedit", aliases=["cedit"])
    @commands.has_role(Config.MODERATOR_ROLE_ID)
    async def filter_edit_condition_command(self, ctx, find: str, new_find: str, new_word: str, new_space_before: str, new_action: str = "warn") -> None:
        found_word_in_filter = False

        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = await self.to_filter_format(find)
        new_find_modified = await self.to_filter_format(new_find)

        if new_space_before == 'y' or new_space_before == 'yes' or new_space_before == 'true' or new_space_before == 't':
            require_space_translated = True
        elif new_space_before == 'n' or new_space_before == 'no' or new_space_before == 'false' or new_space_before == 'f':
            require_space_translated = False
        else:
            raise commands.BadArgument('Invalid answer to space_before. Be sure to define a yes or no answer.')

        for index, word_found in enumerate(filter_data['conditionFilter']):
            if word_found['find'] == find_modified:
                found_word_in_filter = True
                word_found_index = index
                word_found_info = word_found

            elif word_found['find'] == new_find_modified:
                raise WordAlreadyAdded(new_find)

        for word_found in filter_data['conditionFilter']:
            if word_found['find'] == new_find_modified:
                raise WordAlreadyAdded(new_find)

        if not found_word_in_filter:
            raise WordNotFound(find)

        await self.action_type(new_action)

        word_to_edit = {
            'find': new_find_modified,
            'word': new_word,
            'censored': new_word,
            'added_by': word_found_info['added_by'],
            'added_on': word_found_info['added_on'],
            'edited_by': ctx.author.id,
            'edited_on': dt.datetime.utcnow(),
            'require_space': require_space_translated,
            'action': new_action
        }

        filter_data['conditionFilter'][word_found_index] = word_to_edit

        async with aiofiles.open(self.filter_file, "w", encoding="utf-8") as f:
            await f.write(json.dumps(filter_data, cls=chron.DateTimeEncoder))

        self.filter.reload_file()

        await ctx.send(f'Word `{find}` modified to be `{new_find}`.')

    @filter.command(name="list")
    @commands.has_role(Config.MODERATOR_ROLE_ID)
    async def filter_list_command(self, ctx, find: str = 'all') -> None:
        found_word_in_filter = False
        pagemaps = []
        results_per_page = 10

        async with aiofiles.open(self.filter_file, "r", encoding="utf-8") as f:
            filter_data = json.loads(await f.read())

        find_modified = await self.to_filter_format(find)

        if find != 'all':
            for index, word_found in enumerate(filter_data['mainFilter']):
                if word_found['find'] == find_modified:
                    found_word_in_filter = True
                    word_found_index = index

                    await ctx.send(
                        embed=discord.Embed.from_dict(
                            {
                                "title": "Filter Word (Main)",
                                "description": "Note: Words in `find` translated for filter",
                                "color": DEFAULT_EMBED_COLOUR,
                                "author": {"name": "Information"},
                                "footer": {
                                    "text": f"Requested by {ctx.author.display_name} | Result: #{index + 1}",
                                    "icon_url": f"{ctx.author.avatar_url}",
                                },
                                "fields": [
                                    {
                                        "name": "Find",
                                        "value": '||' + await self.from_filter_format(word_found['find']) + '||',
                                        "inline": True,
                                    },
                                    {
                                        "name": "Word",
                                        "value": '||' + word_found['word'] + '||',
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
                                    },
                                ]
                            }
                        )
                    )

                    return


            for index, word_found in enumerate(filter_data['conditionFilter']):
                if word_found['find'] == find_modified:
                    found_word_in_filter = True
                    word_found_index = index
                    main_filter_len = len(filter_data['mainFilter'])

                    await ctx.send(
                        embed=discord.Embed.from_dict(
                            {
                                "title": "Filter Word (Conditional)",
                                "description": "Note: Words in `find` translated for filter",
                                "color": DEFAULT_EMBED_COLOUR,
                                "author": {"name": "Information"},
                                "footer": {
                                    "text": f"Requested by {ctx.author.display_name} | Result: #{index + 1 + main_filter_len}",
                                    "icon_url": f"{ctx.author.avatar_url}",
                                },
                                "fields": [
                                    {
                                        "name": "Find",
                                        "value": '||' + await self.from_filter_format(word_found['find']) + '||',
                                        "inline": True,
                                    },
                                    {
                                        "name": "Word",
                                        "value": '||' + word_found['word'] + '||',
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
                                    },
                                    {
                                        "name": "Space Before",
                                        "value": 'True' if word_found['require_space'] else 'False',
                                        "inline": True,
                                    }
                                ]
                            }
                        )
                    )

                    return

        else:
            list_output = {
                'find': [],
                'word': [],
                'filter': []
            } # type: dict

            for word_found in filter_data['mainFilter']:
                list_output['find'].append(await self.from_filter_format(word_found['find']) + '\n')
                list_output['word'].append(word_found['word'] + '\n')
                list_output['filter'].append('Main\n')

            for word_found in filter_data['conditionFilter']:
                list_output['find'].append(await self.from_filter_format(word_found['find']) + '\n')
                list_output['word'].append(word_found['word'] + '\n')
                list_output['filter'].append('Conditional\n')

            result_count = len(list_output['find'])

            list_output['find'] = await self.chunk_list(list_output['find'], results_per_page)
            list_output['word'] = await self.chunk_list(list_output['word'], results_per_page)
            list_output['filter'] = await self.chunk_list(list_output['filter'], results_per_page)

            found_word_in_filter = True
            num_pages = len(list_output['find'])

            for index, list_pages in enumerate(list_output['find']):
                pagemaps.append(
                    {
                        "title": "Filter List",
                        "description": "Note: Words in `find` translated for filter",
                        "color": DEFAULT_EMBED_COLOUR,
                        "author": {"name": "Information"},
                        "footer": {
                            "text": f"Requested by {ctx.author.display_name} | Page {index + 1} of {num_pages} | Results: {result_count}",
                            "icon_url": f"{ctx.author.avatar_url}",
                        },
                        "fields": [
                            {
                                "name": "Find",
                                "value": '||' + "".join(list_output['find'][index]) + '||',
                                "inline": True
                            },
                            {
                                "name": "Word",
                                "value": '||' + "".join(list_output['word'][index]) + '||',
                                "inline": True
                            },
                            {
                                "name": "Filter",
                                "value": '||' + "".join(list_output['filter'][index]) + '||',
                                "inline": True
                            }
                        ]
                    }
                )

            await FilterListMenu(ctx, pagemaps).start()


        if not found_word_in_filter:
            raise WordNotFound(find)


def setup(bot: commands.Bot) -> None:
    bot.add_cog(Mod(bot))
