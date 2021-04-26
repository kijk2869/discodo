import asyncio

from .errors import VoiceClientNotFound
from .events import DiscordEvent
from .utils import EventDispatcher


class ClientManager:
    def __init__(self, **kwargs):
        self.loop = asyncio.get_event_loop()

        self.id = str(kwargs.get("user_id"))
        self.session_id = str(kwargs.get("session_id"))

        self.voiceClients = {}

        self.dispatcher = EventDispatcher()
        self.discordEvent = DiscordEvent(self)

    def __del__(self):
        for voiceClient in self.voiceClients.values():
            self.loop.call_soon_threadsafe(voiceClient.__del__)

    def __repr__(self):
        return f"<ClientManager id={self.id} session_id='{self.session_id}' voiceClients={len(self.voiceClients)}>"

    def discordDispatch(self, data):
        return self.discordEvent.dispatch(data["t"], data=data["d"])

    def getVC(self, guildID, safe=False):
        if str(guildID) not in self.voiceClients and not safe:
            raise VoiceClientNotFound

        return self.voiceClients.get(str(guildID))

    def delVC(self, guildID: str) -> None:
        self.getVC(guildID).__del__()
