import asyncio
import contextlib
import json
import logging
import uuid

from sanic import Blueprint
from sanic.websocket import ConnectionClosed

from .. import __version__
from ..config import Config
from ..manager import ClientManager
from .payloads import WebsocketPayloads

app = Blueprint(__name__)

log = logging.getLogger("discodo.server.websocket")


@app.websocket("/ws")
async def feedSocket(request, ws) -> None:
    handler = WebsocketHandler(request, ws)
    await handler.join()


class Encoder(json.JSONEncoder):
    @staticmethod
    def default(o):
        return o.toDict()


class ModifiedClientManager(ClientManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._binded = asyncio.Event()


class WebsocketHandler:
    def __init__(self, request, ws):
        self.state = str(uuid.uuid4())
        self.loop = asyncio.get_event_loop()

        self.ws = ws
        self.request = request
        self.app = request.app

        if not hasattr(self.app.ctx, "ClientManagers"):
            self.app.ctx.ClientManagers = {}

        self.ClientManager = None

        self._running = asyncio.Event()
        self.loop.create_task(self.handle())

    def __del__(self):
        if self.ClientManager:
            if self.managerEvent in self.ClientManager.dispatcher._Any:
                self.ClientManager.dispatcher.offAny(self.managerEvent)

            self.loop.create_task(self.waitForBind())

    @property
    def requester(self):
        return f"{self.request.ip}:{self.request.port}"

    async def waitForBind(self):
        if self.state != self.ClientManager.state:
            return

        self.ClientManager._binded.clear()

        try:
            await asyncio.wait_for(
                self.ClientManager._binded.wait(), timeout=Config.VCTIMEOUT
            )
        except asyncio.TimeoutError:
            self.ClientManager.__del__()
            del self.app.ctx.ClientManagers[self.ClientManager.tag]
            self.ClientManager = None

    def join(self):
        return self._running.wait()

    async def sendJson(self, data):
        log.debug(f"{self.requester} < {data}")

        with contextlib.suppress(ConnectionClosed):
            await self.ws.send(json.dumps(data, cls=Encoder))

    async def handle(self):
        if self.request.headers.get("Authorization") != Config.PASSWORD:
            return await self.sendJson({"op": "FORBIDDEN", "d": "Password mismatch."})

        await self.sendJson(
            {
                "op": "HELLO",
                "d": {
                    "version": __version__,
                    "heartbeat_interval": Config.HANDSHAKE_INTERVAL,
                },
            }
        )

        while True:
            try:
                RAWDATA = await asyncio.wait_for(
                    self.ws.recv(), timeout=Config.HANDSHAKE_TIMEOUT
                )
            except (asyncio.TimeoutError, ConnectionClosed) as e:
                if self.managerEvent in self.ClientManager.dispatcher._Any:
                    self.ClientManager.dispatcher.offAny(self.managerEvent)
                return

            try:
                _data = json.loads(RAWDATA)
                log.debug(f"{self.requester} > {_data}")

                Operation, Data = _data.get("op"), _data.get("d")
            except:
                continue

            if Operation and hasattr(WebsocketPayloads, Operation):
                Func = getattr(WebsocketPayloads, Operation)
                self.loop.create_task(self.__run_event(Func, Operation, Data))

    async def __run_event(self, Func, Operation, Data):
        try:
            await Func(self, Data)
        except Exception as e:
            log.exception(
                f"while handle {Func.__name__} on {self.requester}, an error occured."
            )

            payload = {
                "op": Operation,
                "d": {"traceback": {type(e).__name__: str(e)}},
            }

            if "guild_id" in Data:
                payload["d"]["guild_id"] = Data["guild_id"]

            await self.sendJson(payload)

    async def initializeManager(self, user_id, shard_id=None) -> None:
        tag = f"{user_id}{f'-{shard_id}' if shard_id is not None else ''}"

        if tag in self.app.ctx.ClientManagers:
            self.ClientManager = self.app.ctx.ClientManagers[tag]
            self.ClientManager._binded.set()

            self.loop.create_task(self.resumed())
        else:
            self.ClientManager = ModifiedClientManager(user_id=user_id)
            self.ClientManager.tag = tag
            self.app.ctx.ClientManagers[tag] = self.ClientManager

        self.ClientManager.state = self.state
        self.ClientManager.dispatcher.onAny(self.managerEvent)

    async def managerEvent(self, guild_id, **kwargs) -> None:
        await self.sendJson(
            {"op": kwargs.pop("event"), "d": {"guild_id": guild_id, **kwargs}}
        )

    async def resumed(self) -> None:
        payload = {
            "op": "RESUMED",
            "d": {
                "voice_clients": {
                    guild_id: {"id": voiceClient.id, "channel": voiceClient.channel_id}
                    for guild_id, voiceClient in self.ClientManager.voiceClients.items()
                }
            },
        }

        await self.sendJson(payload)
