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
os.remove('creds.json')

sheet = service.spreadsheets().values()
qct = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
cardname = "Card List!C:C"
colname = "Collection!A:A"
collist = "Collection!A:B"
loglist = "Changelog!A:B"

def sheet_get(range):
    return sheet.get(spreadsheetId=qct, range=range).execute().get('values', [])

getcardname = sheet_get(cardname)
getcolname = sheet_get(colname)

def embed_card(embed):
    row = len(getcardname) + 1
    model = embed.title.split()[0]
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

    @staticmethod
    def sheet_append(range, body):
        sheet.append(
                spreadsheetId=qct,
                range=range,
                body=body,
                valueInputOption="USER_ENTERED").execute()

    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        for embed in ctx.embeds:
            #print(embed.to_dict())
            card = embed_card(embed)
            if any(card[2] in i for i in getcardname):
                await ctx.channel.send('data exists')
                continue
            body = {'values': [card]}
            try: sheet_append('Card List!A:Z', body)
            except: await ctx.channel.send('error')
            body = {'values': [[card[2], date.today()]]}
            if 'Fusion' in card[3]: pass
                #sheet_append('Fusion!A:A', [card[2]])
            if not any(card[1] in i for i in  getcolname): pass
                #sheet_append('Collection!A:A', [card[1]])
            await ctx.channel.send('data added')


def setup(bot):
    bot.add_cog(qct(bot))

