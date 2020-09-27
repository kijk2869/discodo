import asyncio
import logging
from typing import Coroutine

import websockets

from ..errors import NodeNotConnected, VoiceClientNotFound
from ..utils import EventDispatcher
from .gateway import NodeConnection
from .voice_client import VoiceClient

log = logging.getLogger("discodo.client")


class Node:
    def __init__(
        self,
        host: str,
        port: int,
        user_id: int = None,
        password: str = "hellodiscodo",
        region: str = None,
    ) -> None:
        self.ws = None
        self.dispatcher = EventDispatcher()
        self.dispatcher.onAny(self.onAnyEvent)

        self.loop = asyncio.get_event_loop()

        self.host = host
        self.port = port
        self.password = password

        self.user_id = user_id
        self.region = region

        self._polling = None
        self.voiceClients = {}
        self.connected = asyncio.Event()

    @property
    def URL(self) -> str:
        return f"ws://{self.host}:{self.port}/ws"

    async def connect(self) -> None:
        if self.connected.is_set():
            raise ValueError("Node already connected")

        if self.ws and not self.ws.closed:
            await self.ws.close()

        self.ws = await NodeConnection.connect(self)
        self.voiceClients = {}
        self.connected.set()

        if not self._polling or self._polling.done():
            self._polling = self.loop.create_task(self.pollingWS())

        if self.user_id:
            await self.ws.send("IDENTIFY", {"user_id": self.user_id})

    @property
    def is_connected(self) -> bool:
        return self.connected.is_set() and self.ws and self.ws.is_connected

    async def destroy(self) -> None:
        if self._polling and not self._polling.done():
            self._polling.cancel()

        if self.ws and not self.ws.closed:
            await self.ws.close()

        self.connected.clear()
        self.voiceClients = {}
        self.ws = None

    async def pollingWS(self) -> None:
        while True:
            try:
                Operation, Data = await self.ws.poll()
            except (asyncio.TimeoutError, websockets.ConnectionClosedError):
                self.connected.clear()

                if self.ws:
                    await self.ws.close()

                self.ws = None
                self.voiceClients = {}
                return

            log.debug(f"event {Operation} dispatched from websocket with {Data}")

            self.dispatcher.dispatch(Operation, Data)

    def send(self, *args, **kwargs) -> Coroutine:
        if not self.ws:
            raise NodeNotConnected

        return self.ws.send(*args, **kwargs)

    async def onAnyEvent(self, Operation, Data):
        if Operation == "RESUMED":
            for voice_client in self.voiceClients:
                voice_client.__del__()

            for guild_id, _ in Data["channels"].items():
                self.voiceClients[int(guild_id)] = VoiceClient(self, guild_id)

        if Operation == "VC_CREATED":
            guild_id = int(Data["guild_id"])
            self.voiceClients[guild_id] = VoiceClient(self, guild_id)

        if Data and isinstance(Data, dict) and "guild_id" in Data:
            vc = self.getVC(Data["guild_id"])
            if vc:
                vc.dispatcher.dispatch(Operation, Data)

        if Operation == "VC_DESTROYED":
            guild_id = int(Data["guild_id"])
            if guild_id in self.voiceClients:
                self.voiceClients[guild_id].__del__()

    def getVC(self, guildID: int, safe: bool = False) -> VoiceClient:
        if not int(guildID) in self.voiceClients and not safe:
            raise VoiceClientNotFound

        return self.voiceClients.get(int(guildID))

    async def discordDispatch(self, payload: dict) -> None:
        if not payload["t"] in [
            "READY",
            "RESUME",
            "VOICE_STATE_UPDATE",
            "VOICE_SERVER_UPDATE",
        ]:
            return

        return await self.send("DISCORD_EVENT", payload)

    async def getStat(self) -> dict:
        await self.send("GET_STAT")

        return await self.dispatcher.wait_for("STAT", timeout=10.0)
