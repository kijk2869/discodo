from logging import getLogger

from .utils import EventEmitter
from .voice_client import VoiceClient

log = getLogger("discodo.event")


class DiscordEvent:
    def __init__(self, client):
        self.client = client

        self.EventEmitter = EventEmitter()

        self.EventEmitter.on("READY", self.parseReady)
        self.EventEmitter.on("RESUME", self.parseResume)
        self.EventEmitter.on("VOICE_STATE_UPDATE", self.parseVoiceStateUpdate)
        self.EventEmitter.on("VOICE_SERVER_UPDATE", self.parseVoiceServerUpdate)

    async def emit(self, event, *args, **kwargs):
        return await self.EventEmitter.emit(event, *args, **kwargs)

    def dispatch(self, event, *args, **kwargs):
        return self.EventEmitter.dispatch(event, *args, **kwargs)

    async def parseReady(self, data):
        log.info(
            f'ready event dispatched. set session id {data["session_id"]} and user id {data["user"]["id"]}'
        )
        self.client.session_id = data["session_id"]
        self.client.user_id = int(data["user"]["id"])

    async def parseResume(self, data):
        log.info(
            f'resume event dispatched. set session id {data["session_id"]} and user id {data["user"]["id"]}'
        )
        self.client.session_id = data["session_id"]
        self.client.user_id = int(data["user"]["id"])

    async def parseVoiceStateUpdate(self, data):
        if not self.client.user_id or data["user_id"] != str(self.client.user_id):
            return
        log.info(f'recieve self voice update. set session id {data["session_id"]}')
        self.client.session_id = data["session_id"]

        if data["channel_id"]:
            self.client.connectedChannels[int(data["guild_id"])] = int(
                data["channel_id"]
            )
        elif int(data["guild_id"]) in self.client.connectedChannels:
            del self.client.connectedChannels[int(data["guild_id"])]

    async def parseVoiceServerUpdate(self, data):
        if int(data["guild_id"]) in self.client.voiceClients:
            log.info(
                f'Voice Client of {data["guild_id"]} found. reconnect to new endpoint'
            )

            vc = self.client.voiceClients[int(data["guild_id"])]
            await vc.createSocket(data)
        else:
            log.info(f'Voice Client of {data["guild_id"]} not found. create new one.')
            vc = VoiceClient(self.client, data)
            self.client.voiceClients[int(data["guild_id"])] = vc

        return vc
