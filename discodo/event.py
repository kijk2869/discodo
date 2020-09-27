import logging

from .utils import EventDispatcher
from .voice_client import VoiceClient

log = logging.getLogger("discodo.event")


class DiscordEvent:
    dispatcher = EventDispatcher()

    def __init__(self, manager) -> None:
        self.manager = manager

        self.dispatcher.on("READY", self.READY)
        self.dispatcher.on("RESUME", self.RESUME)
        self.dispatcher.on("VOICE_STATE_UPDATE", self.VOICE_STATE_UPDATE)
        self.dispatcher.on("VOICE_SERVER_UPDATE", self.VOICE_SERVER_UPDATE)

    def dispatch(self, event: str, *args, **kwargs) -> None:
        return self.dispatcher.dispatch(event, *args, **kwargs)

    async def READY(self, data: dict) -> None:
        log.info(
            f'ready event dispatched. set session id {data["session_id"]} and user id {data["user"]["id"]}'
        )
        self.manager.session_id = data["session_id"]
        self.manager.id = int(data["user"]["id"])

    async def RESUME(self, data: dict) -> None:
        log.info(
            f'resume event dispatched. set session id {data["session_id"]} and user id {data["user"]["id"]}'
        )
        self.manager.session_id = data["session_id"]
        self.manager.id = int(data["user"]["id"])

    async def VOICE_STATE_UPDATE(self, data: dict) -> None:
        if not self.manager.id or data["user_id"] != str(self.manager.id):
            return

        log.info(f'recieve self voice update. set session id {data["session_id"]}')
        self.manager.session_id = data["session_id"]

        if self.manager.getVC(data["guild_id"], safe=True):
            self.manager.getVC(data["guild_id"]).channel_id = (
                int(data["channel_id"]) if data.get("channel_id") else None
            )
        elif data.get("channel_id"):
            log.info(f'Voice Client of {data["guild_id"]} not found. create new one.')

            vc = self.manager.voiceClients[int(data["guild_id"])] = VoiceClient(
                self.manager
            )
            vc.guild_id = int(data["guild_id"])
            vc.channel_id = int(data["channel_id"])

    async def VOICE_SERVER_UPDATE(self, data: dict) -> None:
        if self.manager.getVC(data["guild_id"], safe=True):
            log.info(f"Voice server update recieved. connect to new endpoint")

            await self.manager.getVC(data["guild_id"]).createSocket(data)
        else:
            log.info(f'Voice Client of {data["guild_id"]} not found. create new one.')

            self.manager.voiceClients[int(data["guild_id"])] = VoiceClient(
                self.manager, data
            )
