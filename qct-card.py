import os, requests
from datetime import date
from discord.ext import commands
from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials

# authentication
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

qct = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
cardlist = "Card List!A:Z"
cardname = "Card List!C:C"
collist = "Collection!A:B"
colname = "Collection!A:A"
loglist = "Changelog!A:B"
fusename = "Fusion!A:A"

def sheetappend(r, b):
    sheet.append(spreadsheetId=qct, range=r, body=b, valueInputOption="USER_ENTERED").execute()

sheet.append(spreadsheetId=qct, range='Card List!A:B', body={'majorDimension':'ROWS', 'values':[['test']]}, valueInputOption="USER_ENTERED").execute()

def sheetget(r):
    return sheet.get(spreadsheetId=qct, range=r).execute().get('values', [])

getcardname = sheetget(cardname)
getcolname = sheetget(colname)

def embedcard(embed):
    row = len(getcardname) + 1
    model = embed.title.split()[0] # card model number
    raritype = embed.fields[0].value
    rarity = raritype.replace('Limited ', '')
    ctype = ''
    if 'Limited' in raritype: ctype = 'Limited'
    card = [
            f'=VLOOKUP(B{row}, {collist}, 2, false)',
            embed.footer.text, # 1. collection
            embed.title.replace(model+' ', 'test'), #2. name
            rarity, # 3. rarity
            ctype, # 4. card type
            embed.fields[1].value, # 5. cost
            embed.fields[2].value, # 6. power
            f'=IF(F{row}=0,"∞",ROUNDDOWN(G{row}/F{row},0))',
            f'{embed.fields[3].name} - {embed.fields[3].value}',
            model, # 9. card model number
            f'=VLOOKUP(C{row}, {loglist}, 2, false)']
    return card

class qct(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        for embed in ctx.embeds:
            #print(embed.to_dict())
            card = embedcard(embed)
            if any(card[2] in i for i in getcardname):
                await ctx.channel.send('data exists')
                continue
            body = {
                    'majorDimension':'ROWS', 
                    'values': [card]}
            sheetappend("Card List!A:Z", body)
            body['values'] = [[card[2], str(date.today())]]
            sheetappend(loglist, body)
            if 'Fusion' in card[3]:
                sheetappend(fusename, card[2])
            if not any(card[1] in i for i in  getcolname):
                sheetappend(colname, card[1])
            await ctx.channel.send('data added')

def setup(bot):
    bot.add_cog(qct(bot))
