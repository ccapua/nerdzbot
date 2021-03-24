import discord
from nerdz import Nerdz
import keyring as kr

bot = Nerdz()

@bot.client.event
async def on_ready():
    print(f"Logged in as {bot.client.user}")
    await bot._init()

@bot.client.event
async def on_message(msg):
    await bot.on_message(msg)

@bot.client.event
async def on_disconnect():
    await bot.on_disconnect()

# if this file is the main file
if __name__ == '__main__':
    bot.client.run(kr.get_password('Nerdz bot', 'bot token'))
    