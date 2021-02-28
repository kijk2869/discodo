from .utils import EventDispatcher
from .voice_client import VoiceClient


class DiscordEvent:
    def __init__(self, manager):
        self.manager = manager
        self.dispatcher = EventDispatcher()

        self.dispatcher.on("READY", self.READY)
        self.dispatcher.on("RESUME", self.RESUME)
        self.dispatcher.on("VOICE_STATE_UPDATE", self.VOICE_STATE_UPDATE)
        self.dispatcher.on("VOICE_SERVER_UPDATE", self.VOICE_SERVER_UPDATE)

    def dispatch(self, event, *args, **kwargs):
        return self.dispatcher.dispatch(event, *args, **kwargs)

    async def READY(self, data):
        self.manager.id = int(data["user"]["id"])
        self.manager.session_id = data["session_id"]

    async def RESUME(self, data):
        self.manager.id = int(data["user"]["id"])
        self.manager.session_id = data["session_id"]

    async def VOICE_STATE_UPDATE(self, data):
        if not self.manager.id or int(data["user_id"]) != self.manager.id:
            if self.manager.getVC(data["guild_id"], safe=True):
                vc = self.manager.getVC(data["guild_id"])

                if data.get("channel_id") and int(data["channel_id"]) == vc.channel_id:
                    vc.speakState = False
            return

        self.manager.session_id = data["session_id"]

        if self.manager.getVC(data["guild_id"], safe=True):
            self.manager.getVC(data["guild_id"]).channel_id = (
                int(data["channel_id"]) if data.get("channel_id") else None
            )
        elif data.get("channel_id"):
            vc = self.manager.voiceClients[int(data["guild_id"])] = VoiceClient(
                self.manager
            )
            vc.guild_id = int(data["guild_id"])
            vc.channel_id = int(data["channel_id"])

            vc.dispatcher.dispatch("VC_CREATED", id=vc.id)

    async def VOICE_SERVER_UPDATE(self, data):
        if self.manager.getVC(data["guild_id"], safe=True):
            await self.manager.getVC(data["guild_id"]).createSocket(data)
        else:
            vc = self.manager.voiceClients[int(data["guild_id"])] = VoiceClient(
                self.manager, data
            )

            vc.dispatcher.dispatch("VC_CREATED", id=vc.id)
