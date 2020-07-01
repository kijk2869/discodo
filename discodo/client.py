import asyncio
from .event import DiscordEvent
from .AudioSource import AudioData


class Client:
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.get('user_id')
        self.session_id = kwargs.get('session_id')

        self.voiceClients = {}

        self.discordEvent = DiscordEvent(self)

    async def discordDispatch(self, data):
        Event, Data = data['t'], data['d']

        return await self.discordEvent.dispatch(Event, Data)

    def getVC(self, guildID):
        return self.voiceClients.get(guildID)

    async def getSong(self, Query):
        return await AudioData.create(Query)

    async def loadSong(self, guildID, *args, **kwargs):
        return await self.getVC(guildID).loadSong(*args, **kwargs)
