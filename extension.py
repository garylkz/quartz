import asyncio
import datetime
import json
import os
import random
import re
from typing import Literal

from discord.ext import commands
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials


# Authentication
CREDS = json.loads(os.environ['CREDS'])
SCOPE = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file',
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets'
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(CREDS, SCOPE)
service = discovery.build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

ID = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo' # Not confidential
CARDS = 'Card List!A:M' 
COLS = 'Collection!A:D'
LGCYS = 'Legacy Cards!A:AZ'

DEBUG = False


sheet_append = lambda r, b : sheet.values().append(spreadsheetId=ID, range=r, body={'values': [b]}, valueInputOption='USER_ENTERED').execute()
sheet_update = lambda r, b : sheet.values().update(spreadsheetId=ID, range=r, body={'values': b}, valueInputOption='USER_ENTERED').execute()


def card_album(model: str) -> Literal['Art and Culture', 'History', 'Life on Land', 'Oceans', 'Paleontology', 'Science', 'Space']:
    return (
        'Art and Culture' if model.startswith('AC') else
        'History' if model.startswith(('E', 'MYHI', 'FHI', 'HEV')) else
        'Life on Land' if model.startswith(('L', 'MYLO', 'FLL', 'LEV')) else
        'Oceans' if model.startswith(('O', 'MYSE', 'FSE', 'OEV')) else
        'Paleontology' if model.startswith(('P', 'MYPA', 'FPA', 'PEV')) else
        'Science' if model.startswith(('MYSC', 'FSC', 'CEV')) else
        'Space' if model.startswith(('MYSP', 'FSP', 'SEV')) else ''
    )


def extract(embed) -> list:
    model, name = embed.title.split(' ', 1)
    album = card_album(model)
    collection = embed.footer.text
    value = embed.fields[0].value.split()
    status, rarity = value if 'Limited' in value else ('', value[0])
    cost = embed.fields[1].value
    power = embed.fields[2].value
    ppe = '∞' if cost == '0' else str(int(power)//int(cost))
    ability = description = ''
    if embed.fields[3].name != 'Buffed by':
        ability = embed.fields[3].name
        description = embed.fields[3].value
    return [album, collection, name, status, rarity, cost, power, ppe, ability, description, model]


async def check(message):
    if message.author.id != 739553550224588810: return
    if 'Sorry, unable to process that request' in message.content:
        await message.send('1 hour cooldown')
        await asyncio.sleep(60*60)
        await message.send('Cooldown completed')
    for embed in message.embeds:
        if ( # Embed but not card
            'CUEbot Help' in embed.title or
            re.search('^Results for "(.+)":.*$', embed.title)
        ): return
        card = extract(embed)
        data = sheet.values().batchGet(spreadsheetId=ID, ranges=[CARDS, COLS]).execute().get('valueRanges', [])
        cards, subs = [i['values'] for i in data]
        match, matches = card[10], [i[10] for i in cards] # Kinda slow
        today = str(datetime.date.today())
        # Card check
        if match in matches:
            i = matches.index(match)
            existing = cards[i][:11]
            card[3] = existing[3] # Hierarchy
            if card != existing: # Update card
                legacy = ['Updated'] + existing + [''] + card + [today]
                sheet_append(LGCYS, legacy) # Add legacy
                cards[i] = card + [cards[i][11], embed.image.url]
                sheet_update(CARDS, cards)
                await message.channel.send('Update detected.')
            else: 
                await message.channel.send('Nothing happens.')
                if len(cards[i]) == 12: # Update image, temporary
                    cards[i].append(embed.image.url)
                    sheet_update(CARDS, cards)
                    await message.channel.send('Oh wait, something did.')
        else: # Add card
            sheet_append(CARDS, card + [today, embed.image.url])
            sheet_append('Changelog!A:B', [card[2], today])
            await asyncio.gather(
                message.delete(),
                message.channel.send('New card detected.')
            )
        # Fusion check
        if 'Fusion' in card[3]:
            sheet_append('Fusion!A:A', [card[2]])
            await message.channel.send('Fusion detected.')
        # Collection check
        if card[1] not in [i[0] for i in subs]:
            code = re.search('(^[A-Z]+)[0-9]+$', card[10]).group(1)
            sheet_append(COLS, [card[1], card[0], code, today])
            await message.channel.send('Collection detected.')
        if DEBUG: await message.delete()


# @commands.command('requiem')
# async def restructure(ctx) -> None:
#     models = [i[0] for i in sheet.values().get(spreadsheetId=ID, range='Card List!K:K').execute().get('values', [])]
#     random.shuffle(models)
#     await ctx.send('Begin of a chaos.')
#     for j in models:
#         await ctx.send(f'/find {j}')
#         await asyncio.sleep(20)
#     await ctx.send('Process finished.')


@commands.command('image')
async def update_image_url(ctx) -> None:
    cards = sheet.values().get(spreadsheetId=ID, range=CARDS).execute().get('values', [])
    updates = []
    global DEBUG
    DEBUG = True
    for card in cards:
        if len(card) < 13:
            updates.append(card[10])
    l = len(updates)
    await ctx.send(f'{l} cards to be updated. ({l*20} seconds)')
    await asyncio.sleep(5)
    for model in updates:
        await ctx.send(f'/find {model}')
        await asyncio.sleep(20)
    await ctx.send('Image url finished updating.')
    DEBUG = False


def setup(bot):
    bot.add_listener(check, 'on_message')
    bot.add_command(update_image_url)
    # bot.add_command(restructure)