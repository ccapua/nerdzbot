from __future__ import unicode_literals
from os import startfile
from bs4 import BeautifulSoup
import nacl
import config
from discord import FFmpegPCMAudio
from discord import Game
import os
import requests
from youtube_dl import YoutubeDL
import re
import datetime

class Music():

    class MusicConnection():
        def __init__(self, channel):
            if channel:
                self.playlist = []
                self.playlist_info = []
                self.channel = channel     
            else:
                raise Exception('No channel provided.')

        async def _init(self):
            self.voice_client = await self.channel.connect()

        def add_song(self, filepath, info):
            self.playlist.append(filepath)
            self.playlist_info.append(info)

        def remove_song(self, i):
            filepath = self.playlist[i]
            print(i)
            self.playlist.pop(i)
            self.playlist_info.pop(i)
            os.unlink(filepath)
            


    def __init__(self, client):
        self._client = client
        self._directory = r'C:\Users\ccapu\Documents\Programming\nerdz-bot'
        self._connection = False
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': '%(id)s.%(ext)s',
            'quiet': False
        }
        self._cleanup()

    def _after_playing(self, err):
        if err:
            print(err)
        if self._connection:
            if len(self._connection.playlist) > 1:
                print('Playing next song')
                self._connection.voice_client.play(
                    FFmpegPCMAudio(self._connection.playlist[1]), 
                    after = self._after_playing
                )

            self._connection.remove_song(0)
        
        print('Cleaning up any loose songs')
        self._cleanup()

    def _cleanup(self):
        mp3s = [f for f in os.listdir(self._directory) if f.endswith('.mp3')]
        if self._connection:
            for f in mp3s:
                filepath = os.path.join(self._directory, f)
                loose = True
                for f in self._connection.playlist:
                    if f == filepath:
                        loose = False

                if loose:
                    os.unlink(filepath)
        else:
            for f in mp3s:
                os.unlink(os.path.join(self._directory, f))

    async def _connect(self, channel):
        connection = self.MusicConnection(channel)
        try:
            await connection._init()
        except:
            return False

        self._connection = connection



    def connected(self):
        if self._connection:
            return True
        else:
            return False

    async def leave(self):
        await self._connection.voice_client.disconnect()
        self._connection = False
        self._cleanup()

    async def remove(self, string):
        if self._connection:
            check = re.match(r'\s[\d]+', string)
            print(check)
            if check:
                print(check.group(0))
                self._connection.remove_song(int(check.group(0).strip())-1)
                if check.group(0).strip() == '1':
                    await self.stop()

    def pause(self):
        if self._connection.voice_client.is_playing():
            self._connection.voice_client.pause()

    async def play(self, string, channel, is_file = False):
        is_url = True
        string = string.strip()
        results = {}

        # check if input was a valid string. if not tell youtube-dl to search youtube
        try: requests.get(string)
        except: 
            self.ydl_opts['default_search'] = 'auto'
            is_url = False
        
        # download the audio file
        if is_file:
            pass
        else:
            with YoutubeDL(self.ydl_opts) as ydl:
                if is_url:
                    results = ydl.extract_info(string, download=False)
                else:
                    v_id = ydl.extract_info(string, download=False)['entries'][0]['id']
                    string = f'https://youtube.com/watch?v={v_id}'
                    results = ydl.extract_info(string, download=False)
                    
                ydl.download([string])

        await self._connect(channel)

        if self._connection:
            if is_file:
                filepath = os.path.join(self._directory, string)
                results = {'title': string}
            else:
                filename = results['id'] + '.mp3'
                filepath = os.path.join(self._directory, filename)

            self._connection.add_song(filepath, results)

            if not self._connection.voice_client.is_playing():
                self._connection.voice_client.play(
                    FFmpegPCMAudio(self._connection.playlist[0]),
                    after = self._after_playing
                )
            return True
        else:
            self._cleanup()
            return False

    def playing(self):
        if self._connection:
            return self._connection.playlist_info[0]['title']
        else:
            return False

    def playlist(self):
        if self._connection:
            return [info['title'] for info in self._connection.playlist_info]

    def resume(self):
        if self._connection:
            if self._connection.voice_client.is_paused():
                self._connection.voice_client.resume()
        else:
            raise Exception('No connections.')

    def skip(self):
        if self._connection:
            if len(self._connection.playlist) > 0:
                self._connection.voice_client.stop()
            else:
                self._connection.remove_song(0)
                self._connection.voice_client.disconnect()
                self._connection.voice_client.cleanup()
                self._connection = False
                self._cleanup()

    async def stop(self):
        if self._connection:
            await self._connection.voice_client.disconnect()
            self._connection.voice_client.cleanup()
            self._connection = False
            self._cleanup()