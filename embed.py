import asyncio
from datetime import date
import json
import os
import re
from typing import Awaitable, List

from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

# Authentication
scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive'
]
creds = ServiceAccountCredentials.from_json_keyfile_dict(json.loads(os.environ['CREDS']), scope)

# Goole Sheets service
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

SHEET = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
# 1jxPQD_14rdpJ_kKzWgphcuzjsTYdCpBePbg3mmtxesE
USER = 'USER_ENTERED'

append = lambda r, b, : sheet.values().append(spreadsheetId=SHEET, range=r, body={'values': b}, valueInputOption=USER).execute()
update = lambda r, b, i=SHEET : sheet.values().update(spreadsheetId=SHEET, range=r, body={'values': b}, valueInputOption=USER).execute()

CUE = 739553550224588810
DEBUG = True

CARDS = 'Card List!A:Z'
SUBS = 'Collection!A:D'
LGCYS = 'Legacy Cards!A:Z'


# Debug logging
def debug_log(chn) -> Awaitable:
    async def f(c, *, 
            header: str = 'Debug') -> None:
        print(f'{header}\n{c}')
        await chn.send(f'{header}\n```\n{c}\n```')
    return f


def get_data() -> List[List[str]]:
    data = sheet.values().batchGet(
        spreadsheetId=SHEET,
        ranges = [CARDS, SUBS]
    ).execute().get('valueRanges', [])
    return [i['values'] for i in data]


# Extract card info from embed
def extract(embed) -> list:
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
    return [album, collection, name, status, rarity, cost, power, ppe, ability, description, model]


async def on_embed(msg):
    if msg.author.id != CUE: return # CUE check
    log = debug_log(msg.channel)
    ls = []
    cards, subs = get_data() # Get QCT data
    ns = [i[2].lower() for i in cards]
    try:
        # Search not found check
        notFound = re.search('^Search text "(.+)" not found$', msg.content)
        if notFound:
            n = notFound.group(1).lower()
            if n in ns:
                ls.append('1. EVENT: REMOVE')
                i = ns.index(n)
                lgcy = ['Removed'] + cards[i]
                append(LGCYS, [lgcy])
                del cards[i]
                cards.append([''] * 13)
                update(CARDS, cards)
                await msg.channel.send('Card removed.')
            else:
                ls.append('1. IGNORE: NOT FOUND')
        for embed in msg.embeds:
            # Results check
            if re.search('^Results for ".+":.*', embed.title):
                ls.append('1. IGNORE: RESULTS')
            # Help check
            elif 'CUEbot Help' in embed.title:
                ls.append('1. IGNORE: HELP')
            # Is card check
            elif re.search('[A-Z]+[0-9]+ .+', embed.title):
                card = a, c, n, r, *_ = extract(embed)
                today = str(date.today())
                # Name in list check
                n_ = n.lower()
                inList = n_ in ns
                ls.append('1. NAME IN LIST: ' + str(inList).upper())
                if inList:
                    # Update check
                    i = ns.index(n_)
                    bot = card[:3] + card[4:11]
                    qct = cards[i][:3] + cards[i][4:11]
                    await asyncio.gather(
                        log(bot, header='Latest'),
                        log(qct, header='Current')
                    )
                    if bot == qct:
                        # Url special
                        if len(qct) == 13:
                            ls.append('2. IGNORE: IDENTICAL')
                            await msg.channel.send('Data exist.')
                        else: # Keep until all cards has image url
                            ls.append('2. UPDATE: IMAGE')
                            cards[i].append(embed.image.url)
                            update(CARDS, cards)
                            await msg.channel.send('Easter eggs added.')
                    else: # Update is needed
                        ls.append('2. UPDATE: CARD')
                        lgcy = ['Updated'] + cards[i]
                        append(LGCYS, [lgcy])
                        cards[i] = card[:3] + [cards[i][3]] + card[4:11] + [cards[i][11], embed.image.url]
                        update(CARDS, cards)
                        await msg.channel.send('Card updated.')
                else:
                    # New card detected
                    ls.append('2. APPEND: CARD')
                    append(CARDS, [card + [today]])
                    append('Changelog!A:B', [[n, today]])
                    await msg.channel.send('New card detected.')
                # Fusion check
                if 'Fusion' in r:
                    append('Fusion!A:A', [[n]])
                    await msg.channel.send('Fusion detected.')
                # Collection check
                if not any(c in i[0] for i in subs):
                    p = re.search('(^[A-Z]+)[0-9]+$', card[10]).group(1)
                    append(SUBS, [[c, a, p, today]])
                    await msg.channel.send('Collection detected.')
    except HttpError:
        await msg.channel.send("No 'Editor' permission.")
    # Debug cleanup
    if DEBUG:
        await log('\n'.join(ls))
        await msg.delete()


def setup(bot):
    bot.add_listener(on_embed, 'on_message')