from datetime import date
import os
from random import random
import re

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
sheet = service.spreadsheets().values()

CARDS = 'Card List!A:Z'
CNAMES = 'Card List!C:C'
SUBS = 'Collection!A:B'
SNAMES = 'Collection!A:D'
LOGS = 'Changelog!A:B'

SHEET = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
USER = 'USER_ENTERED'

append = lambda r, b : sheet.append(spreadsheetId=SHEET, range=r, body=b, valueInputOption=USER).execute()
get = lambda r : sheet.get(spreadsheetId=SHEET, range=r).execute().get('values', [])

DEBUG = False

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
    card = [album, collection, name, rarity, status, cost, power, ppe, ability, description, model, log]
    if DEBUG:
        print(card)
    return card

async def on_embed(msg):
    # Only respond to @CUE#3444
    if msg.author.id != 739553550224588810:
        return
    # Embed check
    for embed in msg.embeds:
        if DEBUG:
            print(embed.to_dict())
        card = _, c, n, r, *_ = card_get(embed)
        body = {'values': [card]}
        today = str(date.today())
        if any(n in i for i in get(CNAMES)):
            await msg.channel.send('Data exist.')
        else:
            append(CARDS, body)
            body['values'] = [[n, today]]
            append(LOGS, body)
            await msg.channel.send('Data added.')
            await msg.delete()
        if 'Fusion' in r:
            body['values'] = [[n]]
            append('Fusion!A:A', body)
            await msg.channel.send('Fusion detected.')
        if not any(c in i[0] for i in get(SNAMES)):
            p = re.search('(^[A-Z]+)[0-9]+$', card[10]).group(1)
            body['values'] = [[c, '', p, today]]
            append(SNAMES, body)
            await msg.channel.send('New collection detected.')

def setup(bot):
    bot.add_listener(on_embed, 'on_message')
