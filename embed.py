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
def extract(embed, r: int, date: str) -> list:
    album = f'=VLOOKUP(B{r}, Collection!A:B, 2, false)'
    collection = embed.footer.text
    model, name = embed.title.split(' ', 1)
    value = embed.fields[0].value.split()
    status, rarity = value if 'Limited' in value else ('Standard', value[0])
    cost = embed.fields[1].value
    power = embed.fields[2].value 
    ppe = '∞' if cost == '0' else str(int(power)//int(cost))
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
            await log('EVENT: REMOVE')
            i = ns.index(n)
            card = ['Removed'] + cards[i]
            del cards[i]
            cards.append([''] * 13)
            update(CARDS, cards)
            append(LGCYS, [card])
            await msg.channel.send('Card removed.')
        else:
            await log('IGNORE: NOT FOUND')
        return
    # Embed check
    for embed in msg.embeds:
        # Multiple results check
        if re.search('^Results for ".+":.*', embed.title):
            await log('IGNORE: RESULTS')
            return
        elif 'CUEbot Help' in embed.title:
            await log('IGNORE: HELP')
            return
        # Extract info 
        today = str(date.today())
        card = _, s, n, r, *_ = extract(embed, len(cards)+1, today)
        try:
            n_ = n.lower()
            await log('NAME IN LIST: ' + str(n_ in ns).upper())
            if n_ in ns:
                # Compare data
                i = ns.index(n_)
                await asyncio.gather(
                    log(card, header='Latest'),
                    log(cards[i], header='Existing')
                )
                if card[:11] == cards[i][:11]:
                    await msg.channel.send(f'Data exist.')
                else:
                    await log('EVENT: UPDATE')
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
            if not any(s in i[0] for i in cols):
                p = re.search('(^[A-Z]+)[0-9]+$', card[10]).group(1)
                append(CLTS, [[s, '', p, today]])
                await msg.channel.send('Collection detected.')
        except HttpError:
            await msg.channel.send("No 'Editor' permission.")
        # Debug cleanup
        if DEBUG:
            await msg.delete()


def setup(bot):
    bot.add_listener(on_embed, 'on_message')