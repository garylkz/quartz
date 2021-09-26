import asyncio

async def routine():
    while True:
        await asyncio.sleep(24*60*60) # 24 hours cooldown

def setup(bot):
    bot.add_listener(routine, 'on_ready')