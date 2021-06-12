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
collist = "Collection!A:B"

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

@commands.command()
async def whatis(ctx, *, kwargs):
    for card in cardlist:
        if kwargs.lower() == i.lower(): await ctx.send(i)

def setup(bot):
    bot.add_command(whatis)

