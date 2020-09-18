from .utils import EventDispatcher
from .voice_client import VoiceClient
import logging

log = logging.getLogger("discodo.event")


class DiscordEvent:
    dispatcher = EventDispatcher()

    def __init__(self, manager) -> None:
        self.manager = manager

    def disptach(self, event: str, *args, **kwargs) -> None:
        return self.dispatcher.dispatch(event, *args, **kwargs)

    @dispatcher.event("READY")
    async def READY(self, data: dict) -> None:
        log.info(
            f'ready event dispatched. set session id {data["session_id"]} and user id {data["user"]["id"]}'
        )
        self.manager.session_id = data["session_id"]
        self.manager.id = int(data["user"]["id"])

    @dispatcher.event("RESUME")
    async def RESUME(self, data: dict) -> None:
        log.info(
            f'resume event dispatched. set session id {data["session_id"]} and user id {data["user"]["id"]}'
        )
        self.manager.session_id = data["session_id"]
        self.manager.id = int(data["user"]["id"])

    @dispatcher.event("VOICE_STATE_UPDATE")
    async def VOICE_STATE_UPDATE(self, data: dict) -> None:
        if not self.manager.id or data["user_id"] != str(self.manager.id):
            return log.warning(
                f"recieve self voice update, but user id mismatch, ignored."
            )

        log.info(f'recieve self voice update. set session id {data["session_id"]}')
        self.manager.session_id = data["session_id"]

        self.manager.getVC(data["guild_id"]).channel_id = (
            int(data["channel_id"]) if data.get("channel_id") else None
        )

    @dispatcher.event("VOICE_SERVER_UPDATE")
    async def VOICE_SERVER_UPDATE(self, data: dict) -> None:
        if self.manager.getVC(data["guild_id"]):
            log.info(
                f'Voice Client of {data["guild_id"]} found. reconnect to new endpoint'
            )

            await self.manager.getVC(data["guild_id"]).createSocket(data)
        else:
            log.info(f'Voice Client of {data["guild_id"]} not found. create new one.')

            self.client.voiceClients[int(data["guild_id"])] = VoiceClient(
                self.manager, data
            )
