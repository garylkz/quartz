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

def sheet_append(range, body):
    return sheet.append(
            spreadsheetId=qct,
            range=range,
            body=body,
            valueInputOption="USER_ENTERED").execute()

def sheet_get(range):
    return sheet.get(
            spreadsheetId=qct,
            range=range).execute().get('values', [])

qct = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
cardlist = "Card List!A:Z"
cardname = "Card List!C:C"
colname = "Collection!A:A"
collist = "Collection!A:B"
loglist = "Changelog!A:B"
getcardname = sheet_get(cardname)
getcolname = sheet_get(colname)

def embed_card(embed):
    row = len(getcardname) + 1
    model = embed.title.split()[0]
    raritype = embed.fields[0].value
    rarity = raritype.replace('Limited ', '')
    ctype = 'Standard'
    if 'Limited' in raritype: ctype = 'Limited'
    card = [
            f'=VLOOKUP(B{row}, {collist}, 2, false)',
            embed.footer.text, # 1. collection
            embed.title.replace(model+' ', ''), #2. name
            rarity, # 3. rarity
            ctype, # 4. card type
            embed.fields[1].value, # 5. cost
            embed.fields[2].value, # 6. power
            f'=IF(F{row}=0,"∞",ROUNDDOWN(G{row}/F{row},0))',
            f'{embed.fields[3].name}: {embed.fields[3].value.strip()}',
            model, # 9. card model number
            f'=VLOOKUP(C{row}, {loglist}, 2, false)']
    return card

async def on_embed(msg):
    for embed in msg.embeds:
        #print(embed.to_dict())
        card = embed_card(embed)
        if any(card[2] in i for i in getcardname):
            await msg.channel.send('data exists')
            continue
        body = {'values': [card]}
        sheet_append(cardlist, body)
        body['values'] = [[card[2], str(date.today())]]
        sheet_append(loglist, body)
        if 'Fusion' in card[3]:
            sheet_append('Fusion!A:A', card[2])
        if not any(card[1] in i for i in  getcolname):
            sheet_append(colname, card[1])
        await msg.channel.send('data added')

def setup(bot):
    bot.add_listener(on_embed, 'on_message')

