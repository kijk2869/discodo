import asyncio
import collections
import json
import logging
import time
import warnings
from typing import Optional

import websockets
import websockets.legacy

from .. import __version__

log = logging.getLogger("discodo.client.gateway")


class NodeConnection(websockets.WebSocketClientProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.keepAliver = None
        self.heartbeatTimeout = 60.0

        self.latency: Optional[float] = None
        self.recent_latencies = collections.deque(maxlen=20)

        self._lastAck = self._lastSend = time.perf_counter()

    @classmethod
    async def connect(cls, node, timeout=10.0):
        ws = await asyncio.wait_for(
            websockets.connect(
                node.WS_URL,
                loop=node.loop,
                klass=cls,
                extra_headers={"Authorization": node.password},
            ),
            timeout=timeout,
        )

        ws.Node = node

        return ws

    def __del__(self):
        self.loop.call_soon_threadsafe(lambda: self.loop.create_task(self.close()))

    @property
    def is_connected(self) -> bool:
        return self.open and not self.closed

    @property
    def averagedLatency(self) -> Optional[float]:
        return sum(self.recent_latencies) / len(self.recent_latencies)

    async def sendJson(self, data: dict) -> None:
        await self.send(json.dumps(data))

    async def send(self, data):
        log.debug(f"{self.Node.host}:{self.Node.port} < {data}")
        return await super().send(data)

    async def handleHeartbeat(self):
        while True:
            if self._lastAck + self.heartbeatTimeout < time.perf_counter():
                await self.close(4000)
                return

            await self.sendJson({"op": "HEARTBEAT", "d": int(time.time() * 1000)})

            self._lastSend = time.perf_counter()

            await asyncio.sleep(self.heartbeatInterval)

    async def poll(self):
        message = json.loads(await asyncio.wait_for(self.recv(), timeout=30.0))

        log.debug(f"{self.Node.host}:{self.Node.port} > {message}")

        Operation, Data = message["op"], message.get("d")

        if Operation == "HELLO":
            await self.HELLO(Data)
        elif Operation == "HEARTBEAT_ACK":
            self._lastAck = time.perf_counter()
            self.latency = self._lastAck - self._lastSend
            self.recent_latencies.append(self.latency)

        return Operation, Data

    async def HELLO(self, Data: dict) -> None:
        if Data.get("version") != __version__:
            warnings.warn(
                f"Discodo version mismatch between server and client. (Node {Data.get('version')}/Client {__version__})",
                UserWarning,
            )

        self.heartbeatInterval = min(Data["heartbeat_interval"], 5.0)

        if self.keepAliver and not self.keepAliver.done():
            self.keepAliver.cancel()

        self.keepAliver = self.loop.create_task(self.handleHeartbeat())

    async def close(self, *args, **kwargs):
        if self.keepAliver and not self.keepAliver.done():
            self.keepAliver.cancel()

        await super().close(*args, **kwargs)
