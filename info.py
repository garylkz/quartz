import os, requests
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

def check_card(card):
    sort = '\n'.join(card)
    card = f'''Card```
{sort}```'''
    return card

#card = [album, collection, name, rarity, status, cost, power, ppe, ability name, ability, model, date]
qct = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'

cardlist = sheet_get("Card List!A:Z")
namelist = sheet_get("Card List!C:C")
collist = sheet_get("Collection!A:B")

@commands.command(aliases=['whats'])
async def whatis(ctx, *, kwargs):
    for card in cardlist:
        if any(kwargs.lower() == info.lower() for info in card):
            ability = card[9]
            await ctx.send(check_card(card))
            text = 'Scope```\n'
            if any(i[1] in ability for i in collist):
                text = text + '- Mentioned Album\n'
            if any(i[0] in ability for i in collist):
                text = text + '- Mentioned Collection\n'
            if any(i[0] in ability for i in namelist):
                text = text + f'- Mentioned Card\n'
            text = text + '```'
            await ctx.send(text)

def setup(bot):
    bot.add_command(whatis)

