import asyncio, datetime, json, os, re
import logging
from typing import Literal, List

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

# Sheets API
ID = os.environ['ID']
CARDS = 'Card List!A:M' 
COLS = 'Collection!A:D'
LGCYS = 'Legacy Cards!A:AZ'

sheet_get = lambda r : sheet.values().get(
    spreadsheetId=ID, 
    range=r).execute().get('values', [])

sheet_append = lambda r, b : sheet.values().append(
    spreadsheetId=ID, 
    range=r, 
    body={'values': [b]}, 
    valueInputOption='USER_ENTERED').execute()

sheet_update = lambda r, b : sheet.values().update(
    spreadsheetId=ID, 
    range=r, 
    body={'values': b}, 
    valueInputOption='USER_ENTERED').execute()


def card_album(model: str) -> Literal[
        'Art and Culture', 'History', 'Life on Land', 
        'Oceans', 'Paleontology', 'Science', 'Space']:
    # TODO: Migrate
    AC = ('AC')
    E = ('E', 'MYHI', 'FHI', 'HEV')
    L = ('L', 'MYLO', 'FLL', 'LEV')
    O = ('O', 'MYSE', 'FSE', 'OEV')
    P = ('P', 'MYPA', 'FPA', 'PEV')
    SC = ('MYSC', 'FSC', 'CEV')
    SP = ('MYSP', 'FSP', 'SEV') 
    # old science & space both used 'S' as prefix
    
    predict = ('Art and Culture' if model.startswith(AC) else
               'History' if model.startswith(E) else
               'Life on Land' if model.startswith(L) else
               'Oceans' if model.startswith(O) else
               'Paleontology' if model.startswith(P) else
               'Science' if model.startswith(SC) else
               'Space' if model.startswith(SP) else '')
    return predict


def extract(embed) -> List[str]:
    model, name = embed.title.split(' ', 1)
    album = card_album(model)
    collection = embed.footer.text

    rarity, date, cost, power, *values = [i.value for i in embed.fields]
    status = 'Standard'

    if len(k := rarity.split()) > 1:
        status, rarity = k

    cost.isnumeric() or cost = '0'
    power.isnumeric() or power = '0'
    ppe = '∞' if cost == '0' else str(eval(power + '//' + cost))

    ability = description = ''
    if values: 
        ability = embed.fields[4].name
        description = values[0]
    
    img = embed.image.url

    return [album, collection, name, status, rarity, cost, 
            power, ppe, ability, description, model, date, img]


async def check(message) -> None:
    if message.author.id != 739553550224588810: return
    for embed in message.embeds:
        if ('CUEbot Help' in embed.title or # Embed but not card
            re.search('^Results for "(.+)":.*$', embed.title)): return

        card = extract(embed)
        data = sheet.values().batchGet(
            spreadsheetId=ID, 
            ranges=[CARDS, COLS]).execute().get('valueRanges', [])
        cards, subs = [i['values'] for i in data]

        model, models = card[10], [i[10] for i in cards]
        if model in models: # Existing card check
            i = matches.index(match)
            old = cards[i]
            card[3] = old[3] # Hierarchy
            outcome = 'Nothing happens.'
#            if len(old) < 13:
#                cards[i].append(embed.image.url)
#                sheet_update(CARDS, cards)
#                outcome = 'Something happened.'
            if card != old: # Update card
                legacy = ['Updated'] + old[:-2] + card[:-2]
                sheet_append(LGCYS, legacy) # Add legacy
                cards[i] = card
                sheet_update(CARDS, cards)
                outcome = 'Update detected.'
        else: # New card
            sheet_append(CARDS, card)
            sheet_append('Changelog!A:B', [card[2], card[11]])
            outcome = 'New card detected.'

        await asyncio.gather(message.delete(), message.channel.send(outcome))

        if 'Fusion' in card[3]: # Fusion card
            sheet_append('Fusion!A:A', [card[2]])
            await message.channel.send('Fusion detected.')
        if card[1] not in [i[0] for i in subs]: # New collection
            code = re.search('(^[A-Z]+)[0-9]+$', card[10]).group(1)
            sheet_append(COLS, [card[1], card[0], code, card[11]])
            await message.channel.send('Collection detected.')

# TODO
@commands.command('massupdate')
async def update_all_cards(ctx) -> None:
    cards = sheet_get(CARDS)
    while len(cards) > 0:
        await ctx.send(f'{len(cards)} card(s) left.')
        card = cards.pop(0)
        await ctx.send(f'/find {card[10]}')
        await asyncio.sleep(60)
    await ctx.send('Finished updating.')


@commands.command('image')
async def update_image_url(ctx) -> None:
    cards, updates = sheet_get(CARDS), []
    for card in cards:
        if len(card) < 13:
            updates.append(card[10])
    while len(updates) > 0:
        await ctx.send(f'{len(updates)} card(s) left.')
        update = updates.pop(0)
        await ctx.send(f'/find {update}')
        await asyncio.sleep(60)
    await ctx.send('Finished updating.')


def setup(bot):
    bot.add_listener(check, 'on_message')
    bot.add_command(update_image_url)
    bot.add_command(update_all_cards)
