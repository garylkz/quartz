import asyncio
from datetime import date
import os
import re
from typing import Awaitable, List

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

append = lambda r, b, : sheet.values().append(spreadsheetId=SHEET, range=r, body={'values': b}, valueInputOption=USER).execute()
update = lambda r, b, i=SHEET : sheet.values().update(spreadsheetId=SHEET, range=r, body={'values': b}, valueInputOption=USER).execute()

CARDS = 'Card List!A:Z'
CLTS = 'Collection!A:D'
LGCYS = 'Legacy Cards!A:Z'

DEBUG = True


# Debug logging
def debug_log(chn) -> Awaitable:
    async def f(c, *, 
            header: str = 'Debug') -> None:
        print(c)
        cx = f'{header}\n```\n{c}\n```'
        await chn.send(cx)
    return f


# Extract card info from embed
def extract(embed, date: str) -> list:
    collection = embed.footer.text
    model, name = embed.title.split(' ', 1)
    album = (
        'Art and Culture' if model.startswith(('AC')) else
        'History' if model.startswith(('E', 'MYHI')) else
        'Life on Land' if model.startswith(('L', 'MYLO')) else
        'Oceans' if model.startswith(('O', 'MYSE')) else
        'Paleontology' if model.startswith(('P', 'MYPA')) else
        'Science' if model.startswith(('MYSC')) else
        'Space' if model.startswith(('MYSP')) else ''
    )
    value = embed.fields[0].value.split()
    status, rarity = value if 'Limited' in value else ('', value[0])
    cost = embed.fields[1].value
    power = embed.fields[2].value
    ppe = '∞' if cost == '0' else str(int(power)//int(cost))
    if 'Buffed by' in embed.fields[3].name:
        ability = description = ''
    else:
        ability = embed.fields[3].name
        description = embed.fields[3].value
    url = embed.image.url
    card = [album, collection, name, status, rarity, cost, power, ppe, ability, description, model, date, url]
    return card


async def on_embed(msg):
    # CUE bot check
    if msg.author.id != 739553550224588810:
        return
    # Set debug channel
    log = debug_log(msg.channel)
    ls = []
    # Access qct sheets data
    data = sheet.values().batchGet(
        spreadsheetId=SHEET,
        ranges = [CARDS, CLTS]
    ).execute().get('valueRanges', [])
    cards, cols = [i['values'] for i in data]
    ns = [i[2].lower() for i in cards]
    # Search not found check
    notFound = re.search('^Search text "(.+)" not found$', msg.content)
    if notFound:
        n = notFound.group(1).lower()
        if n in ns:
            ls.append('1. EVENT: REMOVE')
            i = ns.index(n)
            card = ['Removed'] + cards[i]
            del cards[i]
            cards.append([''] * 13)
            update(CARDS, cards)
            append(LGCYS, [card])
            await msg.channel.send('Card removed.')
        else:
            ls.append('1. IGNORE: NOT FOUND')
    # Embed check
    for embed in msg.embeds:
        # Multiple results check
        if (re.search('^Results for ".+":.*', embed.title)
                or 'CUEbot Help' in embed.title):
            ls.append('1. IGNORE: NOT CARD')
        # Is card check
        elif re.search('[A-Z]+[0-9]+ .+', embed.title):
            # Extact info
            today = str(date.today())
            card = _, s, n, r, *_ = extract(embed, today)
            try:
                n_ = n.lower()
                ls.append('1. NAME IN LIST: ' + str(n_ in ns).upper())
                if n_ in ns:
                    # Compare data
                    i = ns.index(n_)
                    await asyncio.gather(
                        log(card, header='Latest'),
                        log(cards[i], header='Current')
                    )
                    latest = (card[:3], card[4:11])
                    current = (cards[i][:3], cards[i][4:11])
                    if current == latest:
                        ls.append('2. IGNORE: IDENTICAL')
                        await msg.channel.send(f'Data exist.')
                    else:
                        ls.append('2. EVENT: UPDATE')
                        pass # TODO: Legacy
                else:
                    ls.append('EVENT: APPEND')
                    append(CARDS, [card])
                    append('Changelog!A:B', [[n, today]])
                    await msg.channel.send('Data added.')
                # Fusion check
                if 'Fusion' in r:
                    append('Fusion!A:A', [[n]])
                    await msg.channel.send('Fusion detected.')
                # Collection check
                if not any(s in i[0] for i in cols):
                    p = re.search('(^[A-Z]+)[0-9]+$', card[10]).group(1)
                    append(CLTS, [[s, '', p, today]])
                    await msg.channel.send('Collection detected.')
            except HttpError:
                await msg.channel.send("No 'Editor' permission.")
    # Debug cleanup
    if DEBUG:
        await log('\n'.join(ls))
        await msg.delete()


def setup(bot):
    bot.add_listener(on_embed, 'on_message')