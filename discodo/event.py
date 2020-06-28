from .utils import EventEmitter
from .voice_client import VoiceClient


class DiscordEvent:
    def __init__(self, client):
        self.client = client

        self.EventEmitter = EventEmitter()

        self.EventEmitter.on('READY', self.parseReady)
        self.EventEmitter.on('RESUME', self.parseResume)
        self.EventEmitter.on('VOICE_STATE_UPDATE', self.parseVoiceStateUpdate)
        self.EventEmitter.on('VOICE_SERVER_UPDATE',
                             self.parseVoiceServerUpdate)

    async def dispatch(self, event, *args, **kwargs):
        return await self.EventEmitter.emit(event, *args, **kwargs)

    async def parseReady(self, data):
        self.client.session_id = data['session_id']

    async def parseResume(self, data):
        self.client.session_id = data['session_id']

    async def parseVoiceStateUpdate(self):
        return

    async def parseVoiceServerUpdate(self, data):
        if data['guild_id'] in self.client.voiceClients:
            vc = self.client.voiceClients[data['guild_id']]
            await vc.createSocket(data)

        vc = VoiceClient(self.client, data)
        self.client.voiceClients[data['guild_id']] = vc

        return vc
