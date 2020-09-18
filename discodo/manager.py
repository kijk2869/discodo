import asyncio

from .errors import VoiceClientNotFound
from .event import DiscordEvent
from .source import AudioData
from .utils import EventDispatcher
from .voice_client import VoiceClient


class ClientManager:
    def __init__(self, **kwargs) -> None:
        self.loop = asyncio.get_event_loop()

        self.id = kwargs.get("user_id")
        self.session_id = kwargs.get("session_id")

        self.voiceClients = {}

        self.event = EventDispatcher()
        self.discordEvent = DiscordEvent()

    def __del__(self) -> None:
        for voiceClient in self.voiceClients.values():
            self.loop.call_soon_threadsafe(voiceClient.__del__)

    def discordDispatch(self, data: dict) -> None:
        Event, Data = data["t"], data["d"]

        return self.discordDispatch.dispatch(Event, Data)

    def getVC(self, guildID: int) -> VoiceClient:
        if not int(guildID) in self.voiceClients:
            raise VoiceClientNotFound

        return self.voiceClients.get(int(guildID))

    def delVC(self, guildID: int) -> None:
        self.getVC(guildID).__del__()

    async def getSource(self, Query: str) -> AudioData:
        return await AudioData.create(Query)

    def putSource(self, guildID: int, *args, **kwargs) -> int:
        return self.getVC(guildID).putSource(*args, **kwargs)

    async def loadSource(self, guildID: int, *args, **kwargs) -> AudioData:
        return await self.getVC(guildID).loadSource(*args, **kwargs)

    def skip(self, guildID: int, offset: int) -> None:
        return self.getVC(guildID).skip(offset)

    async def seek(self, guildID: int, offset: int) -> None:
        return await self.getVC(guildID).seek(offset)

    def setVolume(self, guildID: int, value: float) -> float:
        self.getVC(guildID).volume = value

        return self.getVC(guildID).volume

    def setCrossfade(self, guildID: int, value: float) -> float:
        self.getVC(guildID).crossfade = value

        return self.getVC(guildID).crossfade

    def setGapless(self, guildID: int, value: bool) -> bool:
        self.getVC(guildID).gapless = value

        return self.getVC(guildID).gapless

    def setAutoplay(self, guildID: int, value: bool) -> bool:
        self.getVC(guildID).autoplay = value

        return self.getVC(guildID).autoplay
