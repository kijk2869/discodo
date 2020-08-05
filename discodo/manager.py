import asyncio

from discodo.exceptions import VoiceClientNotFound

from .AudioSource import AudioData
from .event import DiscordEvent
from .utils import EventEmitter
from .voice_client import VoiceClient


class AudioManager:
    def __init__(self, *args, **kwargs):
        self.loop = asyncio.get_event_loop()

        self.user_id = kwargs.get("user_id")
        self.session_id = kwargs.get("session_id")

        self.emitter = EventEmitter()
        self._emitter = EventEmitter()
        self.emitter.onAny(self.onAnyEvent)
        self.event = self._emitter.event

        self.voiceClients = {}
        self.connectedChannels = {}

        self.discordEvent = DiscordEvent(self)

    async def onAnyEvent(self, guild_id, event, *args, **kwargs):
        vc = self.getVC(guild_id)

        self._emitter.dispatch(event, vc, *args, **kwargs)

    def __del__(self):
        for voiceClient in self.voiceClients.values():
            self.loop.call_soon_threadsafe(voiceClient.__del__)

    def discordDispatch(self, data: dict):
        Event, Data = data["t"], data["d"]

        return self.discordEvent.dispatch(Event, Data)

    def getVC(self, guildID: int) -> VoiceClient:
        if not int(guildID) in self.voiceClients:
            raise VoiceClientNotFound

        return self.voiceClients.get(int(guildID))

    def delVC(self, guildID: int):
        self.getVC(guildID).__del__()

    async def getSong(self, Query: str) -> AudioData:
        return await AudioData.create(Query)

    async def putSong(self, guildID: int, *args, **kwargs) -> AudioData:
        return await self.getVC(guildID).putSong(*args, **kwargs)

    async def loadSong(self, guildID: int, *args, **kwargs) -> AudioData:
        return await self.getVC(guildID).loadSong(*args, **kwargs)

    def skip(self, guildID: int, offset: int):
        return self.getVC(guildID).skip(offset)

    def seek(self, guildID: int, offset: int):
        return self.getVC(guildID).seek(offset)

    def setVolume(self, guildID: int, value: float) -> float:
        self.getVC(guildID).volume = value

        return self.getVC(guildID).volume

    def setCrossfade(self, guildID: int, value: float) -> float:
        self.getVC(guildID).crossfade = value

        return self.getVC(guildID).crossfade

    def setAutoplay(self, guildID: int, value: bool) -> bool:
        self.getVC(guildID).autoplay = value

        return self.getVC(guildID).autoplay
