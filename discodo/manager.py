import asyncio
from .errors import VoiceClientNotFound
from .event import DiscordEvent
from .voice_client import VoiceClient


class ClientManager:
    def __init__(self, **kwargs) -> None:
        self.loop = asyncio.get_event_loop()

        self.id = kwargs.get("user_id")
        self.session_id = kwargs.get("session_id")

        self.voiceClients = {}

        self.event = None
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