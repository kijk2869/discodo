import asyncio
import json
import logging
import os
from asyncio.tasks import wait_for

from sanic import Blueprint
from sanic.websocket import ConnectionClosed

from ...manager import AudioManager
from .events import WebsocketEvents

WSINTERVAL = float(os.getenv("WSINTERVAL", "15"))
WSTIMEOUT = float(os.getenv("WSTIMEOUT", "60"))
VCTIMEOUT = float(os.getenv("VCTIMEOUT", "300.0"))
PASSWORD = os.getenv("PASSWORD", "hellodiscodo")

log = logging.getLogger("discodo.server")


app = Blueprint(__name__)


@app.websocket("/")
async def feed(request, ws):
    handler = WebsocketHandler(request, ws)
    await handler.join()


class ModifyAudioManager(AudioManager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._binded = asyncio.Event()


class WebsocketHandler:
    def __init__(self, request, ws):
        self.loop = asyncio.get_event_loop()
        self.request = request
        self.ws = ws

        if not hasattr(request.app, "AudioManagers"):
            request.app.AudioManagers = {}

        self.AudioManager = None

        self.loop.create_task(self.handle())
        self._running = asyncio.Event()

    def __del__(self):
        if self.AudioManager:
            self.loop.create_task(self.wait_for_bind())

    async def wait_for_bind(self):
        self.AudioManager._binded.clear()

        try:
            await asyncio.wait_for(self.AudioManager._binded.wait(), timeout=VCTIMEOUT)
        except asyncio.TimeoutError:
            self.AudioManager.__del__()
            del self.request.app.AudioManagers[int(self.AudioManager.user_id)]
            self.AudioManager = None

    async def join(self):
        return await self._running.wait()

    async def handle(self):
        if self._running.is_set():
            self._running.clear()

        try:
            await self._handle()
        finally:
            self._running.set()
            self.__del__()

    async def _handle(self):
        log.info(f"new websocket connection created from {self.request.ip}.")

        if self.request.headers.get("Authorization") != PASSWORD:
            log.warning(
                f"websocket connection from {self.request.ip} forbidden: password mismatch."
            )
            await self.forbidden("Password mismatch.")
            return

        await self.hello()

        while True:
            try:
                RAWDATA = await asyncio.wait_for(self.ws.recv(), timeout=WSTIMEOUT)
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

            if Operation and hasattr(WebsocketEvents, Operation):
                log.debug(f"{Operation} dispatched with {Data}")

                Func = getattr(WebsocketEvents, Operation)
                self.loop.create_task(Func(self, Data))

    async def sendJson(self, Data):
        log.debug(f"send {Data} to websocket connection of {self.request.ip}.")
        await self.ws.send(json.dumps(Data))

    async def initialize_manager(self, user_id):
        if int(user_id) in self.request.app.AudioManagers:
            self.AudioManager = self.request.app.AudioManagers[int(user_id)]
            self.AudioManager._binded.set()
            self.loop.create_task(self.resumed())
            log.debug(f"AudioManager of {user_id} resumed.")
        else:
            self.AudioManager = ModifyAudioManager(user_id=user_id)
            self.request.app.AudioManagers[int(user_id)] = self.AudioManager
            log.debug(f"AudioManager of {user_id} intalized.")

        self.AudioManager.emitter.onAny(self.manager_event)

    async def manager_event(self, guild_id, Event, **kwargs):
        payload = {"op": Event, "d": {"guild_id": guild_id}}
        payload["d"] = dict(payload["d"], **kwargs)

        await self.sendJson(payload)

    async def hello(self):
        payload = {"op": "HELLO", "d": {"heartbeat_interval": WSINTERVAL}}

        await self.sendJson(payload)

    async def forbidden(self, message):
        payload = {"op": "FORBIDDEN", "d": message}

        await self.sendJson(payload)

    async def resumed(self):
        payload = {
            "op": "RESUMED",
            "d": {
                "voice_clients": [
                    (guild_id, self.AudioManager.connectedChannels.get(guild_id),)
                    for guild_id, voiceClient in self.AudioManager.voiceClients.items()
                ]
            },
        }

        await self.sendJson(payload)
