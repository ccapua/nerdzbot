from __future__ import unicode_literals
from os import startfile
from bs4 import BeautifulSoup
import nacl
import config
import discord, os, random, requests, requests.auth, subprocess, time, youtube_dl

# Get a discord client
client = discord.Client()

# Set download options for youtube_dl
ydl_opts = {
    'format': 'bestaudio/best',
    'default_search': 'ytsearch',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }]
}
# Get a youtube_dl object to work with later
ydl = youtube_dl.YoutubeDL(ydl_opts)

# Set up for the reddit bot - oauth2 handshake and token send
response = requests.get("https://oauth.reddit.com/api/v1/authorize?client_id=A-MR4_6jEdSDYg&response_type=application/json&state=geezerd00d&redirect_uri=https://discordapp.com/oauth2/authorize?client_id=612094661447909377&scope=bot&permissions=36776960&duration=permanent&scope=read")
print(response.content)

# What to do when the bot's ready
@client.event
async def on_ready():
  print(f"Logged in as {client.user}")

# MESSAGE EVENTS
@client.event
async def on_message(msg):

  # Help document
  if msg.content == 'n!help':
    await msg.channel.send(""" 
    Here are some commands \n
    n!eat - prints a random restaurant in martin by default or the town you enter \n
    n!joke - prints a random dad joke \n
    n!purge - purges the current channel of all messages. add a space followed by a number for a specific number of messages \n
    n!reddit - prints the top 5 posts from a given subreddit \n
    """)

  # Clean pancake messages
  if msg.content.startswith('p!'):
    await msg.delete()
  
  if msg.author.name == 'Pancake':
    await msg.delete()

  # Clean nerdzbot messages
  if msg.content.startswith('n!'):
    await msg.delete()

  if msg.author.name == 'nerdz':
    time.sleep(30)
    await msg.delete()
  
  # Random restaurant in Martin or another place you specify (thru Yelp API)
  if msg.content.startswith('n!eat'):
    headers={'Authorization': 'Bearer 1FbB9IgIaikfshg3WWqVkS7CA6Z0XSyf8yyrSjc4Ly2KQGtUQ8O4-0t1Hm-YFKDVh3Rq6z0Ai7dNRtesAuPtGmwIBGmAoRzBYbitZX6izkN_Rat0CUS6_hXLBlRkXHYx'}
    if msg.content[5:]:
      response = requests.get('https://api.yelp.com/v3/businesses/search?location=' + msg.content[5:], headers=headers)
    else:
      response = requests.get('https://api.yelp.com/v3/businesses/search?location=Martin, TN', headers=headers)

    response = response.json()
    restaurant = response['businesses'][random.randint(0, len(response['businesses']))]['name']
    await msg.channel.send(restaurant)

  # Random joke from icanhazdadjoke
  if msg.content == 'n!joke':
    joke = requests.get('https://icanhazdadjoke.com/', headers={'Accept': 'application/json'})
    joke = joke.json()
    await msg.channel.send(joke['joke'])

  
  # Reddit - Top 5 posts from a given subreddit
  if msg.content.startswith('n!reddit'):
    response = requests.get('https://oauth.reddit.com/r/' + msg.content[9:] + "/api/info", )
    src = response.content
    soup = BeautifulSoup(src, "html5lib")

    print(soup.prettify())

  # Purging messages
  if msg.content.startswith('n!purge'):
    if msg.content[8:]:
      await msg.channel.purge(limit=int(msg.content[8:]))
    else:
      await msg.channel.purge()

  # YOUTUBE/MUSIC STUFF
  if msg.content.startswith('n!play'):
    if msg.content[7:]:
      connection = await msg.author.voice.channel.connect()
      result = ydl.extract_info(msg.content[7:], download=False)
      ydl.download([msg.content[7:]])
      filename = result['title'] + '-' + result['id'] + '.mp3'

      connection.play(discord.FFmpegPCMAudio(filename), after=lambda filename: os.remove(filename))

  if msg.content == 'n!pause':
    for x in client.voice_clients:
      if x.is_playing():
        x.pause()

  if msg.content == 'n!resume':
    for x in client.voice_clients:
      if x.is_paused():
        x.resume()

  if msg.content == 'n!stop':
    for x in client.voice_clients:
      await x.disconnect()

client.run(config.BOT_TOKEN)