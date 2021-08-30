from datetime import date
import os
import re

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
sheet = service.spreadsheets().values()

CARDS = 'Card List!A:Z'
CNAMES = 'Card List!C:C'
SUBS = 'Collection!A:B'
SNAMES = 'Collection!A:D'
LOGS = 'Changelog!A:B'

SHEET = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
USER = 'USER_ENTERED'

append = lambda r, b, i=SHEET : sheet.append(spreadsheetId=i, range=r, body=b, valueInputOption=USER).execute()
get = lambda r : sheet.get(spreadsheetId=SHEET, range=r).execute().get('values', [])


IDS = []
appends = lambda r, b, i : [append(r, b, i) for i in IDS]

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
    url = embed.image.url
    card = [album, collection, name, rarity, status, cost, power, ppe, ability, description, model, log, url]
    if DEBUG:
        print(card)
    return card

async def on_embed(msg):
    # @CUE#3444 check
    if msg.author.id != 739553550224588810:
        return
    # Card not found check
    if re.search('^Search text ".*" not found$', msg.content):
      await msg.channel.send('Potential card removal')
      # TODO: move card to Legacy
    # Embed check
    for embed in msg.embeds:
        if DEBUG:
            print(embed.to_dict())
        card = _, c, n, r, *_ = card_get(embed)
        body = {'values': [card]}
        today = str(date.today())
        try:
            cards = get(CARDS)
            names = [i[2] for i in cards]
            if n in names:
                i = names.index(n)
                if card == cards[i]:
                    await msg.channel.send(f'Data exist. (row {i})')
                else:
                    await msg.channel.send('>existing data outdated\n>move it to legacy section\n>replace')
                    # TODO: move card to Legacy
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
        except HttpError:
            await msg.channel.send("But I don't have permission to edit the sheet!")

def setup(bot):
    bot.add_listener(on_embed, 'on_message')
