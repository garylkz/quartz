import os, requests
from datetime import date
from discord.ext import commands
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

open('creds.json', 'w').write(requests.get(os.environ['link']).text)
scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets().values()
os.remove('creds.json')

def sheet_get(range):
    return sheet.get(
            spreadsheetId=qct,
            range=range).execute().get('values', [])

qct = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
cardlist = sheet_get("Card List!A:Z")
namelist = sheet_get("Card List!C:C")
collist = sheet_get"Collection!A:B")

"""
card = [
        album,
        collection,
        name,
        rarity,
        type,
        cost,
        power,
        ppe,
        ability,
        model,
        date]
"""

@commands.command(aliases=['whats'])
async def whatis(ctx, *, kwargs):
    for card in cardlist:
        if any(kwargs.lower() == info.lower() for info in card):
            await ctx.send(card)
            targetcard, targetcol, targetalb = False, False, False
            if any(i[1] in card[8] for i in collist): targetalb = True
            if any(i[0] in card[8] for i in collist): targetcol = True
            if any(i[0] in card[8] for i in namelist): targetcard = True
            await ctx.send(f'''
```
Scope
Album: {targetalb}
Collection: {targetcol}
Card: {targetcard}
```
                    ''')

def setup(bot):
    bot.add_command(whatis)

