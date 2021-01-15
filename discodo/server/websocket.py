import asyncio
import json
import logging
from typing import Coroutine

from sanic import Blueprint
from sanic.websocket import ConnectionClosed

from .. import __version__
from ..config import Config
from ..manager import ClientManager
from .payloads import WebsocketPayloads

log = logging.getLogger("discodo.server")

app = Blueprint(__name__)


@app.websocket("/ws")
async def socket_feed(request, ws) -> None:
    handler = WebsocketHandler(request, ws)
    await handler.join()


class Encoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__()


class ModifiedClientManager(ClientManager):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self._binded = asyncio.Event()


class WebsocketHandler:
    def __init__(self, request, ws) -> None:
        self.loop = asyncio.get_event_loop()

        self.request = request
        self.ws = ws
        self.app = request.app

        if not hasattr(self.app, "ClientManagers"):
            self.app.ClientManagers = {}

        self.ClientManager = None

        self._running = asyncio.Event()
        self.loop.create_task(self._handle())

    def __del__(self) -> None:
        if self.ClientManager:
            self.ClientManager.dispatcher.offAny(self.manager_event)

            self.loop.create_task(self.wait_for_bind())

    async def wait_for_bind(self) -> None:
        self.ClientManager._binded.clear()

        try:
            await asyncio.wait_for(
                self.ClientManager._binded.wait(), timeout=Config.VCTIMEOUT
            )
        except asyncio.TimeoutError:
            self.ClientManager.__del__()
            del self.app.ClientManagers[int(self.ClientManager.id)]
            self.ClientManager = None

    def join(self) -> Coroutine:
        return self._running.wait()

    async def _handle(self) -> None:
        log.info(f"new websocket connection created from {self.request.ip}.")

        if self.request.headers.get("Authorization") != Config.PASSWORD:
            log.warning(
                f"websocket connection from {self.request.ip} forbidden: password mismatch."
            )
            return await self.forbidden("Password mismatch.")

        await self.hello()

        while True:
            try:
                RAWDATA = await asyncio.wait_for(
                    self.ws.recv(), timeout=Config.HANDSHAKE_TIMEOUT
                )
            except (asyncio.TimeoutError, ConnectionClosed) as exception:
                if isinstance(exception, asyncio.TimeoutError):
                    log.info("websocket connection closing because of timeout.")
                elif isinstance(exception, ConnectionClosed):
                    log.info(
                        f"websocket connection disconnected. code {exception.code}"
                    )

                return

            try:
                _Data = json.loads(RAWDATA)
                Operation, Data = _Data.get("op"), _Data.get("d")
            except:
                continue

            if Operation and hasattr(WebsocketPayloads, Operation):
                log.debug(f"{Operation} dispatched with {Data}")

                Func = getattr(WebsocketPayloads, Operation)
                self.loop.create_task(self.__run_event(Func, Operation, Data))

    async def __run_event(self, Func: Coroutine, Operation: str, Data) -> None:
        try:
            await Func(self, Data)
        except Exception as e:
            payload = {
                "op": Operation,
                "d": {"traceback": {type(e).__name__: str(e)}},
            }

            if "guild_id" in Data:
                payload["d"]["guild_id"] = Data["guild_id"]

            await self.sendJson(payload)

    async def sendJson(self, Data: dict) -> None:
        log.debug(f"send {Data} to websocket connection of {self.request.ip}.")
        try:
            await self.ws.send(json.dumps(Data, cls=Encoder))
        except ConnectionClosed:
            log.debug(
                f"while sending data to websocket connection of {self.request.ip}, the connection closed, ignored."
            )

    async def initialize_manager(self, user_id: int) -> None:
        if int(user_id) in self.app.ClientManagers:
            self.ClientManager = self.app.ClientManagers[int(user_id)]
            self.ClientManager._binded.set()

            self.loop.create_task(self.resumed())
            log.debug(f"ClientManager of {user_id} resumed.")
        else:
            self.ClientManager = ModifiedClientManager(user_id=user_id)
            self.app.ClientManagers[int(user_id)] = self.ClientManager

            log.debug(f"ClientManager of {user_id} intalized.")

        self.ClientManager.dispatcher.onAny(self.manager_event)

    async def manager_event(self, guild_id: int, **kwargs) -> None:
        Event = kwargs.pop("event")

        payload = {"op": Event, "d": {"guild_id": guild_id}}
        payload["d"] = dict(payload["d"], **kwargs)

        await self.sendJson(payload)

    async def hello(self) -> None:
        payload = {
            "op": "HELLO",
            "d": {
                "version": __version__,
                "heartbeat_interval": Config.HANDSHAKE_INTERVAL,
            },
        }

        await self.sendJson(payload)

    async def forbidden(self, message: str) -> None:
        payload = {"op": "FORBIDDEN", "d": message}

        await self.sendJson(payload)

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
