import os
import wake

from discord.ext import commands
from replit import info

wake.up(info.co_url)

bot = commands.Bot(',')
bot.load_extension('extension')

@bot.command()
async def find(ctx, *, con):
	await ctx.send(f'/find {con}')

bot.run(os.environ['TOKEN'])