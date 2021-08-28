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

CARDS = 'Card List!A:Z'
CNAMES = 'Card List!C:C'
SUBS = 'Collection!A:B'
SNAMES = 'Collection!A:A'
LOGS = 'Changelog!A:B'

SHEET_ID = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
USER = 'USER_ENTERED'

append = lambda r, b : sheet.append(spreadsheetID=SHEET_ID, range=r, body=b, valueInputOption=USER)

# def sheet_append(r: str, b: dict) -> None:
#     return sheet.append(
#             spreadsheetId=SHEET_ID, 
#             range=r,
#             body=b, 
#             valueInputOption='USER_ENTERED'
#     ).execute()

def sheet_get(r: str) -> dict:
    return sheet.get(
            spreadsheetId=SHEET_ID,
            range=r
    ).execute().get('values', [])

DEBUG = False

# Sort out card info from embed
def card_get(embed) -> list:
    ROWS = len(sheet_get(CARDS)) + 1
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
        card = card_get(embed)
        cname = card[2]
        if any(cname in i for i in sheet_get(CNAMES)):
            await msg.channel.send('Data exist.')
        else:
            body = {'values': [card]}
            append(CARDS, body)
            body['values'] = [[cname, str(date.today())]]
            append(LOGS, body)
            await msg.channel.send('Data added.')
            if 'Fusion' in card[3]:
                body['values'] = [[cname]]
                append('Fusion!A:A', body)
                await msg.channel.send('Fusion detected.')
            if not any(card[1] in i for i in sheet_get(SNAMES)):
                body['values'] = [[card[1]]]
                append(SNAMES, body)
                await msg.channel.send('New collection detected.')
            await msg.delete()

def setup(bot):
    bot.add_listener(on_embed, 'on_message')
