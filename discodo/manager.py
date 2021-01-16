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

        self.Context = {}
        self.voiceClients = {}

        self.dispatcher = EventDispatcher()
        self.event = self.dispatcher.event
        self.discordEvent = DiscordEvent(self)

    def __del__(self) -> None:
        for voiceClient in self.voiceClients.values():
            self.loop.call_soon_threadsafe(voiceClient.__del__)

    def __repr__(self) -> str:
        return f"<ClientManager id={self.id} session_id='{self.session_id}' voiceClients={len(self.voiceClients)}>"

    def discordDispatch(self, data: dict) -> None:
        Event, Data = data["t"], data["d"]

        return self.discordEvent.dispatch(Event, data=Data)

    def getVC(self, guildID: int, safe: bool = False) -> VoiceClient:
        if int(guildID) not in self.voiceClients and not safe:
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
