import os
from random import random
from datetime import date

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

debug = False
SHEET_ID = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
CARDS = 'Card List!A:Z'
CNAMES = 'Card List!C:C'
SUBS = 'Collection!A:B'
SNAMES = 'Collection!A:A'
LOGS = 'Changelog!A:B'

def set_debug(status=True):
    global debug
    debug = status

def sheet_append(r, b):
    sheet.append(
            spreadsheetId=SHEET_ID, 
            range=r, body=b, 
            valueInputOption='USER_ENTERED'
    ).execute()

def sheet_get(r):
    return sheet.get(
            spreadsheetId=SHEET_ID,
            range=r
    ).execute().get('values', [])

def card_get(embed):
    ROWS = len(sheet_get(CARDS)) + 1
    album = f'=VLOOKUP(B{ROWS}, {SUBS}, 2, false)'
    collection = embed.footer.text
    model, name = embed.title.split(' ', 1)
    if debug: name += str(random())[2:]
    value = embed.fields[0].value.split()
    status, rarity = value if 'Limited' in value else ('', value[0])
    cost = embed.fields[1].value
    power = embed.fields[2].value 
    ppe = '∞' if cost == '0' else str(int(power)//int(cost))
    ability = embed.fields[3].name
    description = embed.fields[3].value
    log = str(date.today())
    return [album, collection, name, rarity, status, cost, power, ppe, ability, description, model, log]

async def on_embed(msg):
    if msg.author.id != 739553550224588810: return 
    for embed in msg.embeds:
        if debug: print(embed.to_dict())
        card = card_get(embed)
        cname = card[2]
        if any(cname in i for i in sheet_get(CARDS)):
            await msg.channel.send('`Your opinion has been rejected.` (data exist)')
            continue
        body = {'values': [card]}
        sheet_append(CARDS, body)
        body['values'] = [[cname, str(date.today())]]
        sheet_append(LOGS, body)
        await msg.channel.send('Card data added.')
        if 'Fusion' in card[3]:
            body['values'] = [[cname]]
            sheet_append('Fusion!A:A', body)
            await msg.channel.send('Fusion detected.')
        if not any(card[1] in i for i in sheet_get(SNAMES)):
            body['values'] = [[card[1]]]
            sheet_append(SNAMES, body)
            await msg.channel.send('New collection detected.')
        await msg.channel.send('Thank you for your contribution.')
        await msg.delete()

def setup(bot):
    bot.add_listener(on_embed, 'on_message')
