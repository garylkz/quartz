import asyncio
from datetime import date
import os
import re
from typing import Awaitable

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

# Authentication
CREDS = 'creds.json'
open(CREDS, 'w').write(os.environ['CREDS'])
scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
]
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS, scope)
os.remove(CREDS)

# Goole Sheets service
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

SHEET = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
USER = 'USER_ENTERED'

append = lambda r, b, i=SHEET : sheet.values().append(spreadsheetId=i, range=r, body={'values': b}, valueInputOption=USER).execute()
get = lambda r : sheet.values().get(spreadsheetId=SHEET, range=r).execute().get('values', [])
update = lambda r, b, i=SHEET : sheet.values().update(spreadsheetId=i, range=r, body={'values': b}, valueInputOption=USER).execute()
appends = lambda r, b, ids : [append(r, b, i) for i in ids]

CARDS = 'Card List!A:Z'
SNAMES = 'Collection!A:D'
LGCYS = 'Legacy Cards!A:Z'

DEBUG = True


async def on_embed(msg):
    # Bot check
    if msg.author.id != 739553550224588810:
        return
    # Set debug channel
    debug_log = debug_init(msg.channel)
    # Get existing data
    cards = get(CARDS)
    names = [i[2].lower() for i in cards]
    # Card not found check
    notFound = re.search('^Search text "(.*)" not found$', msg.content)
    if notFound:
        n = notFound.group(1).lower()
        if n in names:
            await debug_log('EVENT: REMOVE')
            i = names.index(n)
            card = cards.pop(i)
            cards.append([''] * 13)
            update(CARDS, cards)
            append(LGCYS, [['Removed'] + card])
            await msg.channel.send('Card removed.')
        else:
            await debug_log('IGNORE: NOT FOUND')
        return
    # Embed check
    for embed in msg.embeds:
        if re.search('^Results for ".+":.*', embed.title):
            await debug_log('IGNORE: RESULTS')
            return # Ignore 'results'
        card = _, c, n, r, *_ = card_get(embed)
        today = str(date.today())
        try: # Permission check
            nx = n.lower()
            await debug_log(f'NAME IN LIST: {nx in names}')
            if nx in names:
                i = names.index(nx)
                await asyncio.gather(
                    debug_log(card, header='CUE Bot'),
                    debug_log(cards[i], header='Sheet')
                )
                if card == cards[i]:
                    await msg.channel.send(f'Data exist.')
                else: # Update event
                    await debug_log('EVENT: UPDATE')
                    pass # TODO: Legacy
            else:
                append(CARDS, [card])
                append('Changelog!A:B', [[n, today]])
                await msg.channel.send('Data added.')
            # Fusion check
            if 'Fusion' in r:
                append('Fusion!A:A', [[n]])
                await msg.channel.send('Fusion detected.')
            # Collection check
            if not any(c in i[0] for i in get(SNAMES)):
                p = re.search('(^[A-Z]+)[0-9]+$', card[10]).group(1)
                append(SNAMES, [[c, '', p, today]])
                await msg.channel.send('Collection detected.')
        except HttpError:
            await msg.channel.send("No 'Editor' permission.")
        # Debug cleanup
        if DEBUG:
            await msg.delete()


# Debug logging
def debug_init(chn) -> Awaitable:
    async def f(c, *, 
            header: str = 'Debug') -> None:
        print(c)
        cx = f'{header}\n```\n{c}\n```'
        await chn.send(cx)
    return f


# Sort out card info from embed
def card_get(embed) -> list:
    ROWS = len(get(CARDS)) + 1
    album = f'=VLOOKUP(B{ROWS}, Collection!A:B, 2, false)'
    collection = embed.footer.text
    model, name = embed.title.split(' ', 1)
    value = embed.fields[0].value.split()
    status, rarity = value if 'Limited' in value else ('Standard', value[0])
    cost = embed.fields[1].value
    power = embed.fields[2].value 
    ppe = '∞' if cost == '0' else str(int(power)//int(cost))
    ability = embed.fields[3].name
    description = embed.fields[3].value
    log = str(date.today())
    url = embed.image.url
    card = [album, collection, name, status, rarity, cost, power, ppe, ability, description, model, log, url]
    return card


def setup(bot):
    bot.add_listener(on_embed, 'on_message')