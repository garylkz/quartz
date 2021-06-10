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
os.remove('creds.json')

sheet = service.spreadsheets().values()
qct = '1JL8Vfyj4uRVx6atS5njJxL03dpKFkgBu74u-h0kTNSo'
clist = 'Card List!'
col = 'Collection!'
fuse = 'Fusion!'
log = 'Changelog!'
getcardlist = sheet.get(spreadsheetId=qct, range='Card List!A:A').execute().get('values', [])

def sheet_append(r, data):
    sheet.append(
            spreadsheetId=qct, 
            range=r, 
            body=data, 
            valueInputOption="USER_ENTERED").execute()

def sheet_get(r):
    return sheet.get(
            spreadsheetId=qct,
            range=r).execute().get('values', [])

def embed_card(embed):
    x =
    row = len(getcardlist) + 1
    model = embed.title.split()[0] # card model number
    raritype = embed.fields[0].value
    rarity = raritype.replace('Limited ', '')
    ctype = ''
    if 'Limited' in raritype: ctype = 'Limited'
    card = [
            f'=VLOOKUP(B{row}, {col}A:B, 2, false)',
            embed.footer.text, # 1. collection
            embed.title.replace(model+' ', ''), #2. name
            rarity, # 3. rarity
            ctype, # 4. card type
            embed.fields[1].value, # 5. cost
            embed.fields[2].value, # 6. power
            f'=IF(F{row}=0,"∞",ROUNDDOWN(G{row}/F{row},0))',
            f'{embed.fields[3].name} - {embed.fields[3].value}',
            model, # 9. card model number
            f'=VLOOKUP(C{row}, {log}A:B, 2, false)']
    return card

class qct(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, ctx):
        await self.bot.process_commands(ctx)
        for embed in ctx.embeds:
            #print(embed.to_dict()) # debug
            card = embed_card(embed)
            if card[2] in sheet_get(clist+'C:C'):
                await ctx.channel.send('data exists')
                continue
            data = {
                    'majorDimension':'ROWS', 
                    'values': [card]}
            sheet_append(clist+'A:Z', data)
            data['values'] = [[card[2], str(date.today())]]
            sheet_append(log+'A:B', data)
            if 'Fusion' in card[3]:
                sheet_append(fuse+'A:A', card[2])
            if card[1] not in sheet_get(col+'A:A'):
                sheet_append(col+'A:A', card[1])
            await ctx.channel.send('data added')

def setup(bot):
    bot.add_cog(qct(bot))
