from .event import DiscordEvent
from .AudioSource import AudioData
from .utils import EventEmitter
from .voice_client import VoiceClient


class AudioManager:
    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.get('user_id')
        self.session_id = kwargs.get('session_id')

        self.event = EventEmitter()

        self.voiceClients = {}

        self.discordEvent = DiscordEvent(self)

    async def discordEmit(self, data: dict):
        Event, Data = data['t'], data['d']

        return await self.discordEvent.emit(Event, Data)

    def discordDispatch(self, data: dict):
        Event, Data = data['t'], data['d']

        return self.discordEvent.dispatch(Event, Data)

    def getVC(self, guildID: int) -> VoiceClient:
        return self.voiceClients.get(guildID)

    async def getSong(self, Query: str) -> AudioData:
        return await AudioData.create(Query)

    async def putSong(self, guildID: int, *args, **kwargs) -> AudioData:
        return await self.getVC(guildID).putSong(*args, **kwargs)

    async def loadSong(self, guildID: int, *args, **kwargs) -> AudioData:
        return await self.getVC(guildID).loadSong(*args, **kwargs)

    def setVolume(self, guildID: int, value: float) -> float:
        self.getVC(guildID).volume = value

        return self.getVC(guildID).volume

    def setCrossfade(self, guildID: int, value: float) -> float:
        self.getVC(guildID).crossfade = value

        return self.getVC(guildID).crossfade
