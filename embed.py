from datetime import date
import os
import re
from typing import ClassVar

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

open('creds.json', 'w').write(os.environ['CREDS'])
scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
]
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
os.remove('creds.json')

service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

CARDS = 'Card List!A:Z'
CNAMES = 'Card List!C:C'
SUBS = 'Collection!A:B'
SNAMES = 'Collection!A:D'
LGCYS = 'Legacy Cards!A:Z'
LOGS = 'Changelog!A:B'

SHEET = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
USER = 'USER_ENTERED'

append = lambda r, b, i=SHEET : sheet.values().append(spreadsheetId=i, range=r, body={'values': b}, valueInputOption=USER).execute()
get = lambda r : sheet.values().get(spreadsheetId=SHEET, range=r).execute().get('values', [])
update = lambda r, b, i=SHEET : sheet.values().update(spreadsheetId=i, range=r, body={'values': b}, valueInputOption=USER).execute()

appends = lambda r, b, ids : [append(r, b, i) for i in ids]

DEBUG = True


# Debug logging
def debug_init(chn):
    async def f(c, *, 
            header: str = None) -> None:
        if DEBUG:
            print(c)
            c = f'```\n{c}\n```'
            x = f'{header}\n{c}' if header else c
            await chn.send(x)
    return f


# Sort out card info from embed
def card_get(embed) -> list:
    ROWS = len(get(CARDS)) + 1
    album = f'=VLOOKUP(B{ROWS}, {SUBS}, 2, false)'
    collection = embed.footer.text
    model, name = embed.title.split(' ', 1)
    value = embed.fields[0].value.split()
    status, rarity = value if 'Limited' in value else ('', value[0])
    cost = embed.fields[1].value
    power = embed.fields[2].value 
    ppe = '∞' if cost == '0' else str(int(power)//int(cost))
    ability = embed.fields[3].name
    description = embed.fields[3].value
    log = str(date.today())
    url = embed.image.url
    card = [album, collection, name, rarity, status, cost, power, ppe, ability, description, model, log, url]
    return card


async def on_embed(msg):
    # @CUE#3444 check
    if msg.author.id != 739553550224588810:
        return
    # Set debug channel
    debug_log = debug_init(msg.channel)
    # Card not found check
    notFound = re.search('^Search text "(.*)" not found$', msg.content)
    if notFound:
        name = notFound.group(1)
        cards = get(CARDS)
        names = [i[2] for i in cards]
        if name in names:
            i = names.index(name)
            card = cards.pop(i)
            cards.append([''] * 13)
            update(CARDS, cards)
            append(LGCYS, [['Removed'] + card])
            await msg.channel.send('Card removed, moving to Legacy.')
        else:
            await debug_log('IGNORE', header='Event')
        return
    # Embed check
    for embed in msg.embeds:
        # Results check
        if re.search('^Results for ".*"$', embed.title):
            await debug_log('IGNORE', header='Event')
            return
        card = _, c, n, r, *_ = card_get(embed)
        today = str(date.today())
        try:
            cards = get(CARDS)
            names = [i[2] for i in cards]
            if n in names:
                i = names.index(n)
                await debug_log(card, header='CUE Bot')
                await debug_log(cards[i], header='Sheet')
                if card == cards[i]:
                    await msg.channel.send(f'Data exist.')
                else:
                    pass # TODO: Legacy
            else:
                append(CARDS, [card])
                append(LOGS, [[n, today]])
                await msg.channel.send('Data added.')
            if 'Fusion' in r:
                append('Fusion!A:A', [[n]])
                await msg.channel.send('Fusion detected.')
            if not any(c in i[0] for i in get(SNAMES)):
                p = re.search('(^[A-Z]+)[0-9]+$', card[10]).group(1)
                append(SNAMES, [[c, '', p, today]])
                await msg.channel.send('New collection detected.')
        except HttpError:
            await msg.channel.send("But I don't have permission to edit the sheet!")
        # Debug cleanup
        if DEBUG:
            await msg.delete()


def setup(bot):
    bot.add_listener(on_embed, 'on_message')