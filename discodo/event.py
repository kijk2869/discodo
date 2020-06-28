from .utils import EventEmitter
from .voice_client import VoiceClient
from logging import getLogger

log = getLogger('discodo.event')


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
        log.info(f'ready event dispatched. set session id {data["session_id"]}')
        self.client.session_id = data['session_id']

    async def parseResume(self, data):
        log.info(f'resume event dispatched. set session id {data["session_id"]}')
        self.client.session_id = data['session_id']

    async def parseVoiceStateUpdate(self, data):
        return

    async def parseVoiceServerUpdate(self, data):
        if int(data['guild_id']) in self.client.voiceClients:
            log.info(f'Voice Client of {data["guild_id"]} found. reconnect to new endpoint')

            vc = self.client.voiceClients[int(data['guild_id'])]
            await vc.createSocket(data)
        else:
            log.info(f'Voice Client of {data["guild_id"]} not found. create new one.')
            vc = VoiceClient(self.client, data)
            self.client.voiceClients[int(data['guild_id'])] = vc

        return vc
