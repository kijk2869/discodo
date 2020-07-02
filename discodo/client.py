import asyncio
from .event import DiscordEvent
from .AudioSource import AudioData


class Client:
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.get('user_id')
        self.session_id = kwargs.get('session_id')

        self.voiceClients = {}

        self.discordEvent = DiscordEvent(self)

    async def discordEmit(self, data):
        Event, Data = data['t'], data['d']

        return await self.discordEvent.emit(Event, Data)

    async def discordDispatch(self, data):
        Event, Data = data['t'], data['d']

        return await self.discordEvent.dispatch(Event, Data)

    def getVC(self, guildID):
        return self.voiceClients.get(guildID)

    async def getSong(self, Query):
        return await AudioData.create(Query)

    async def putSong(self, guildID, *args, **kwargs):
        return await self.getVC(guildID).putSong(*args, **kwargs)

    async def loadSong(self, guildID, *args, **kwargs):
        return await self.getVC(guildID).loadSong(*args, **kwargs)
    
    def setVolume(self, guildID, value):
        self.getVC(guildID).volume = value

        return self.getVC(guildID).volume
    
    def setCrossfade(self, guildID, value):
        self.getVC(guildID).crossfade = value

        return self.getVC(guildID).crossfade
