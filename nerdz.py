from __future__ import unicode_literals
from os import startfile
from bs4 import BeautifulSoup
import nacl
import config
import discord
import os
import random
import requests
import time
from youtube_dl import YoutubeDL
import re
import datetime
import asyncio
from urllib.parse import parse_qs
import keyring
# my imports
from music import Music 
import texas_hold_em

class Nerdz():

    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        self.yelp_bearer = keyring.get_password('Yelp', 'bearer token')
        self.client = discord.Client(intents=intents)
        self.music_handler = Music(self.client)
        self.hold_em = False

    async def _init(self):
        await self.client.change_presence(status=discord.Status.online, activity=discord.Game(name='nothing.'))

    async def change_song_status(self, name):
        if name != False and name != '':
            await self.client.change_presence(activity = discord.Game(name='nothing.'))
        else:
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game(name=name))

    async def on_disconnect(self):
        pass

    async def on_message(self, msg):
        #region auto_message_cleaning
        if msg.content.lower().startswith('p!'): await msg.delete()
        if msg.author.name == 'Pancake': await msg.delete()
        if msg.content.lower().startswith('n!'): await msg.delete()
        #endregion auto_message_cleaning
        #region holdem_setup_prompts
        if self.hold_em and self.hold_em._channel == msg.channel:
            if self.hold_em.state == 'waiting for player list':
                names = msg.content.lower().split(' ')
                users = []
                for name in names:
                    for u in self.client.users:
                        if name == u.display_name.lower():
                            users.append(u)

                if len(users) > 0:
                    await self.hold_em.generate_players(users)          
            elif self.hold_em.state == 'waiting for money amount':
                try:
                    if int(msg.content) > 0:
                        await self.hold_em.set_money(int(msg.content.lower()))
                except:
                    pass    
        #endregion holdem_setup_prompts
        if msg.content.lower().startswith('n!'):
            command_strings = msg.content.lower()[2:].split(' ')
            command = command_strings[0]
            print(' '.join(command_strings))
            #region help
            if command == 'help':
                command = msg.content.lower()[6:].strip().lower()
                
                if len(command) == 0:
                    await msg.channel.send(
                        "**NERDZ-BOT**\n" +
                        "*Type **n!help** followed by a space and one of the following commands*"
                        "\nmusic\n" +
                        "> Audio player commands\n" +
                        "\nmisc\n" +
                        "> Miscellaneous commands.\n" +
                        "\ntarkov\n" +
                        "> Tarkov commands (mostly just displays maps and ammo chart)\n" +
                        "\nwow\n" +
                        "> Wow commands (only wowhead search implemented)\n" +
                        "\ncleanup\n"
                        "> Commands for cleaning up text channel messages\n",
                        delete_after=120
                    )

                if command == 'music':
                    await msg.channel.send(
                        "**MUSIC COMMANDS**\n" +
                        "*Type **n!music** followed by a space and one of the following commands:*\n" +
                        "*Do not type [] brackets when typing commands.*\n" +
                        "\nplay [*youtube search string or a youtube url*]\n" +
                        "> if no url, grabs first search result with input, downloads audio, and adds to playlist\n" +
                        "> otherwise, downloads url and adds to playlist\n" +
                        "\nplaying\n" +
                        "> returns the name of the currently playing audio\n" +
                        "\nleave\n" +
                        "> forces the bot to leave your current voice channel. deletes the playlist\n"
                        "\npause\n" +
                        "> pauses. can be resumed with n!music resume\n" +
                        "\nremove [*number in playlist*]\n" +
                        "> removes the song at the number in the playlist\n" +
                        "> if is currently playing song, skips to next\n" +
                        "\nresume\n" +
                        "> resumes if paused\n"
                        "\nskip\n" +
                        "> removes current song from playlist and plays next song in playlist\n" +
                        "\nstop\n" +
                        "> stops playing, disconnects bot, and deletes the playlist if any\n",
                        delete_after=120
                    ) # double check skip (I think something was wrong??)

                if command == 'misc':
                    await msg.channel.send(
                        "**MISCELLANEOUS COMMANDS**\n" +
                        "*Type **n!misc** followed by a space and one of the following commands*\n"
                        "*Do not type [] brackets when typing commands.*\n"
                        "\neat [*optional location (city, st)*]\n" +
                        "> prints a random restaurant in martin by default or the town you enter.\n" +
                        "\njoke\n" +
                        "> prints a random dad joke.\n" 
                        "\nrimshot\n" +
                        "> plays a rimshot...\n",
                        delete_after=120
                    ) # fix string matching on eat places

                    # find a random picture (maybe with a search string?) look for an api
                    # come up with some other stuff to add
                    # n!eyebleach (always sfw) look for an api

                if command == 'tarkov':
                    await msg.channel.send(
                        "**TARKOV COMMANDS**\n" +
                        "*Type **n!tarkov** followed by a space and one of the following commands*\n" +
                        "*Do not type [] brackets when typing commands\n" +
                        "\n[*a map name*]\n" +
                        "> posts a picture of the map given\n" +
                        "> map names: customs, factory, interchange, reserve, shoreline, labs, woods\n" +
                        "\nammo\n" +
                        "> posts a picture of the ammo comparison chart\n",
                        delete_after=120
                    )

                if command == 'wow':
                    await msg.channel.send(
                        "**WOW COMMANDS**\n" +
                        "*Type **n!wow** followed by a space and one of the following commands*\n" +
                        "*Do not type [] brackets when typing commands\n" +
                        "\nsearch [*a search string*]\n" +
                        "> returns first google search result on wowhead for the search string\n" +
                        "> searches retail by default. to specify classic prepend search string with 'classic' (no quotes)\n",
                        delete_after=120
                    )

                if command == 'cleanup':
                    await msg.channel.send(
                        "**CLEANUP COMMANDS**\n" +
                        "*Type **n!cleanup** followed by a space and one of the following commands.*\n" +
                        "*Note that cleanup only happens in the channel in which you call the command.*\n"
                        "*Do not type [] brackets when typing commands.*\n" +
                        "\n[nothing]\n" +
                        "> searches for any nerdz-bot messages in the last 500 messages and deletes them.\n" +
                        "\n[*a number, x*]\n" +
                        "> searches for any nerdz-bot messages in the last x messages and deletes them.\n" +
                        "\nall\n" +
                        "> removes any messages from nerdz-bot in this text channel ever."
                        "> *not recommended* Can potentially take a very long time to complete.\n" +
                        "> The bot may not receive commands while this happens.\n"
                        "\nuser [*a username*] [*a number, x*]\n" +
                        "> searches for any messages matching the username provided in the last x messages and deletes them.\n"
                        "\nany [*a number, x*]\n" +
                        "> removes the past x messages, regardless of author.\n",
                        delete_after=120
                    ) # if someone is banned delete every message from every channel by them
            #endregion help
            #region holdem
            elif command == 'holdem':
                command_strings = msg.content.lower()[8:].split(' ')
                command_strings.pop(0)

                if len(command_strings) > 0:
                    command = command_strings[0]
                    command_strings.pop(0)

                    #region game commands
                    if command == 'play' and not self.hold_em:
                        await msg.channel.send(
                            "Tell me who's playing (display name (in this server) separated by spaces).", 
                            delete_after=120
                        )
                        self.hold_em = texas_hold_em.Game(msg.channel)
                    elif command == 'end' and self.hold_em != False:
                        await msg.channel.send('Game over.')
                        self.hold_em = False
                    #endregion game commands
                    #region player commands
                    elif command == 'check' and self.hold_em:
                        await self.hold_em.check(msg.author.display_name)
                    elif command == 'bet' and self.hold_em:
                        try:
                            num = int(command_strings[0])
                            await self.hold_em.bet(num, msg.author.display_name)
                        except:
                            await msg.channel.send(
                                '(Type n!holdem bet [*a number here*].)',
                                delete_after=30
                            )
                    elif command == 'call' and self.hold_em:
                        await self.hold_em.call(msg.author.display_name)
                    elif command == 'fold' and self.hold_em:
                        await self.hold_em.fold(msg.author)
                    elif command == 'reveal' and self.hold_em:
                        pass
                    elif command == 'muck' and self.hold_em:
                        pass
                    #endregion player commands
                    #region debug
                    elif command == 'deck' and self.hold_em:
                        await self.hold_em.deck()
                    #endregion debug
                    else:
                        await msg.channel.send(
                            'Holdem command not recognized...', 
                            delete_after=30
                        )
            #endregion holdem
            #region tarkov
            elif command == 'tarkov':
                tark_dir = r'C:\Users\ccapu\Documents\Games\Tarkov'
                command = msg.content.lower()[8:].strip().lower()
                if len(command) > 0:
                    with open(os.path.join(tark_dir, f'{command.capitalize()}.png'), 'rb') as f:
                        picture = discord.File(f)
                        await msg.channel.send(file=picture) 
            #endregion tarkov
            #region wow   
            elif command == 'wow':
                command_strings = msg.content.lower()[5:].split(' ')
                command_strings.pop(0)

                if command_strings[0] == 'search':
                    command_strings.pop(0)
                    
                    if command_strings[0] == 'classic':
                        command_strings.pop(0)
                        string = ' '.join(command_strings)
                        url = f'https://www.google.com/search?q={string}+site%3Aclassic.wowhead.com'
                    else:
                        string = ' '.join(command_strings)
                        url = f'https://www.google.com/search?q={string}+site%3Awww.wowhead.com'

                    r = requests.get(url)
                    soup = BeautifulSoup(r.text)
                    send = [e.get('href') for e in soup.find_all('a') if ('wowhead.com' in e.get('href') and e.get('href').startswith('/url?q='))][0]
                    await msg.channel.send(send[7:], delete_after=120)
            #endregion wow
            #region music 
            elif command == 'music':
                command_strings = msg.content.lower()[7:].split(' ')
                command_strings.pop(0)

                if len(command_strings) > 0:
                    command = command_strings[0].strip()
                    command_strings.pop(0)

                    channel = msg.author.voice.channel

                    if command == 'play' and channel:
                        command_strings.pop(0)
                        print(command_strings)
                        string = ' '.join(command_strings).strip()
                        print(string)
                        if not await self.music_handler.play(string, channel):
                            await msg.channel.send("Something went wrong. Make sure you're in a voice channel")
                        await self.change_song_status(self.music_handler.playing())

                    elif command == 'remove':
                        command_strings.pop(0)
                        if len(command_strings):
                            await self.music_handler.remove(command_strings[0])

                    elif command == 'pause':
                        self.music_handler.pause()

                    elif command == 'stop':
                        await self.music_handler.stop()
                        await self.change_song_status('')

                    elif command == 'skip':
                        self.music_handler.skip()
                        await self.change_song_status(self.music_handler.playing())

                    elif command == 'leave':
                        await self.music_handler.leave()
                        await self.change_song_status('')

                    elif command == 'resume':
                        self.music_handler.resume()

                    elif command == 'playing':
                        await msg.channel.send(self.music_handler.playing(), delete_after=120)

                    elif command == 'playlist':
                        if self.music_handler.connected():    
                            i = 1
                            await msg.channel.send('**PLAYLIST ORDER**', delete_after=120)
                            for title in self.music_handler.playlist():
                                await msg.channel.send(
                                    f'> {i}:     {title}\n',
                                    delete_after=120
                                )
                                i = i + 1
                    else:
                        await msg.channel.send('n!help music')
                else:
                    await msg.channel.send('n!help music')
            #endregion music
            #region misc
            elif command == 'misc':
                command_strings = msg.content[6:].split(' ')
                command_strings.pop(0)
                command = command_strings.pop(0)

                if command == 'eat':
                    string = ' '.join(command_strings)
                    headers = {'Authorization': f'Bearer {self.yelp_bearer}'}

                    if len(command_strings) > 0:
                        r = requests.get(
                            'https://api.yelp.com/v3/businesses/search?location=' + 
                            string, 
                            headers=headers
                        )
                    else:
                        r = requests.get(
                            'https://api.yelp.com/v3/businesses/search?location=Martin, TN'
                            , headers=headers
                        )
                    r = r.json()
                    restaurant = r['businesses'][random.randint(0, len(r['businesses']))]['name']
                    await msg.channel.send(restaurant, delete_after=120)
                # Random joke from icanhazdadjoke
                elif command == 'joke':
                    r = requests.get(
                        'https://icanhazdadjoke.com/', 
                        headers={'Accept': 'application/json'}
                    )
                    joke = r.json()

                    await msg.channel.send(
                        joke['joke'], 
                        delete_after=120
                    )
                # it plays a rimshot
                elif command == 'rimshot':
                    await self.music_handler.play(
                        r'C:\Users\ccapu\Documents\sounds\rimshot.mp3', 
                        msg.author.voice.channel, 
                        is_file = True
                    )
                else:
                    await msg.channel.send('n!help misc')
            #endregion misc
            #region donkey
            elif command == 'donkey':
                with open('donkey.gif', 'rb') as f:
                    picture = discord.File(f)
                    await msg.channel.send(file=picture, delete_after=120)             
            #endregion donkey
            #region cleanup
            elif command == 'cleanup':
                command_strings = msg.content.lower()[9:].split(' ')
                command_strings.pop(0)

                if len(command_strings) == 0:
                    await msg.channel.purge(
                        check = lambda m: m.author == self.client.user,
                        limit = 500,
                        oldest_first = False
                    )
                    return
                elif len(command_strings) > 0:
                    try:
                        num = int(command_strings[1])
                        await msg.channel.purge(
                            check = lambda m: m.author == self.client.user,
                            limit = num,
                            oldest_first = False
                        )
                    except:
                        pass
            
                    # all
                    if command_strings[0] == 'all':
                        await msg.channel.purge(
                            check = lambda m: m.author == self.client.user,
                            oldest_first = False
                        )
                    # any
                    if command_strings[0] == 'any' and len(command_strings) > 1:
                        try:
                            num = int(command_strings[1])
                            await msg.channel.purge(
                                limit = num,
                                oldest_first = False
                            )
                        except:
                            pass
                    # user
                    if command_strings[0] == 'user' and len(command_strings) > 2:
                        name = command_strings[1]
                        try:
                            num = int(command_strings[2])
                            await msg.channel.purge(
                                check = lambda m: m.author.display_name == name,
                                limit = num,
                                oldest_first = False
                            )
                        except:
                            return
                else:
                    await msg.channel.send('n!help cleanup')
            #endregion cleanup
            # in case they typed a wrong command
            else:
                await msg.channel.send('n!help', delete_after=120)