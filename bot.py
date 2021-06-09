from discord.ext import commands

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

import os, requests

# authentication
open('creds.json', 'w').write(requests.get(os.environ['link']).text)
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive.file','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', scope)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets().values()
os.remove('creds.json')

# variables
qct = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
cardNameList = sheet.get(spreadsheetId=qct,range='Card List!C:C').execute().get('values', [])
cardColList = sheet.get(spreadsheetId=qct,range='Card List!A:A').execute().get('values', [])

bot = commands.Bot('')

@bot.event
async def on_message(ctx):
    for embed in ctx.embeds: # detect embed
        #print(embed.to_dict()) # debug
        card = cardInfo(embed)
        if any(card[2] in i for i in cardNameList):
            await ctx.channel.send('Card data exists')
        else:
            # card section
            data = {
                    'majorDimension':'ROWS', 
                    'values': [card]}
            append('Card List!A:Z', data) # line 48
            await ctx.channel.send('card added')
            # changelog section
            append('Changelog!A:A', card[2])
            # fusion section
            if card[3] == 'fusion':
                append('Fusion!A:A', card[2])
            # new collection?
            if any(card[1] in i for i in cardColList):
                append('Collection!A:A', card[1])
                await ctx.channel.send(card[1])
            await ctx.channel.send('Card data added')
    await bot.process_commands(ctx)

def cardInfo(embed):
    row = str(len(cardNameList)+1) # new row
    model = embed.title.split()[0] # card model number
    raritype = embed.fields[0].value
    rarity = raritype.replace('Limited ', '')
    if 'Limited' in raritype: ctype = 'Limited'
    else: ctype = ''
    card = [
            '=VLOOKUP(B'+row+', Collection!A:B, 2, false)', # 0. album formula
            embed.foot9er.text, # 1. collection
            embed.title.replace(model+' ', ''), # 2. name
            rarity, # 3. rarity
            ctype, # 4. type
            embed.fields[1].value, # 5. cost
            embed.fields[2].value, # 6. power
            '=IF(F'+row+'=0,"∞",ROUNDDOWN(G'+row+'/F'+row+',0))', #7. ppe formula
            embed.fields[3].name + " - " + embed.fields[3].value, # 8. ability formula
            model, # 9. model
            '=VLOOKUP(C'+row+', Changelog!A:B, 2, false)'] # 10. date formula
    return card

@bot.command()
async def ping(ctx):
    await ctx.send('pong')

def append(range, data):
    sheet.append(spreadsheetId=qct, range=range, body=data, valueInputOption="USER_ENTERED").execute()

bot.run(os.environ['TOKEN'])
