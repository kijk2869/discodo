import asyncio
import collections
import contextlib
import inspect
import json
import logging
import struct
import time
from typing import Optional

import websockets
import websockets.legacy

from .enums import VoicePayload
from .natives import Cipher

log = logging.getLogger("discodo.gateway")


class VoiceSocket(websockets.WebSocketClientProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.keepAliver = None
        self.heartbeatTimeout = 60.0

        self.latency: Optional[float] = None
        self.recent_latencies = collections.deque(maxlen=20)

        self._lastAck = self._lastSend = time.perf_counter()

    @classmethod
    async def connect(cls, client, resume=False) -> websockets.WebSocketClientProtocol:
        ws = await websockets.connect(
            f"wss://{client.endpoint}/?v=4",
            loop=client.loop,
            klass=cls,
            compression=None,
        )

        ws.client = client

        if not resume:
            await ws.identify()  # type: ignore
        else:
            await ws.resume()  # type: ignore

        return ws

    def __del__(self):
        self.loop.call_soon_threadsafe(lambda: self.loop.create_task(self.close()))

    @property
    def averagedLatency(self) -> Optional[float]:
        return sum(self.recent_latencies) / len(self.recent_latencies)

    async def sendJson(self, data: dict) -> None:
        await self.send(json.dumps(data))

    async def send(self, data):
        log.debug(f"{self.client.endpoint} < {data}")
        return await super().send(data)

    async def handleHeartbeat(self):
        with contextlib.suppress(websockets.ConnectionClosedError):
            while True:
                if self._lastAck + self.heartbeatTimeout < time.perf_counter():
                    await self.close(4000)
                    return

                await self.sendJson(
                    {"op": VoicePayload.HEARTBEAT.value, "d": int(time.time() * 1000)}
                )

                self._lastSend = time.perf_counter()

                await asyncio.sleep(self.heartbeatInterval)

    async def identify(self):
        payload = {
            "op": VoicePayload.IDENTIFY.value,
            "d": {
                "server_id": str(self.client.guild_id),
                "user_id": str(self.client.user_id),
                "session_id": self.client.session_id,
                "token": self.client.token,
            },
        }
        await self.sendJson(payload)

    async def resume(self):
        payload = {
            "op": VoicePayload.RESUME.value,
            "d": {
                "server_id": str(self.client.guild_id),
                "user_id": str(self.client.user_id),
                "session_id": self.client.session_id,
                "token": self.client.token,
            },
        }
        await self.sendJson(payload)

    async def select_protocol(self, ip: str, port: str, mode: str):
        payload = {
            "op": VoicePayload.SELECT_PROTOCOL.value,
            "d": {
                "protocol": "udp",
                "data": {"address": ip, "port": port, "mode": mode},
            },
        }
        await self.sendJson(payload)

    async def speak(self, state: bool = True):
        self.client.speakState = state

        payload = {
            "op": VoicePayload.SPEAKING.value,
            "d": {"speaking": int(state), "delay": 0, "ssrc": self.client.ssrc},
        }
        await self.sendJson(payload)

    async def messageRecieved(self, message):
        log.debug(f"{self.client.endpoint} > {message}")
        Operation, Data = VoicePayload(message["op"]), message.get("d")

        if Operation == VoicePayload.READY:
            await self.createConnection(Data)
        elif Operation == VoicePayload.HEARTBEAT_ACK:
            self._lastAck = time.perf_counter()
            self.latency = self._lastAck - self._lastSend
            self.recent_latencies.append(self.latency)
        elif Operation == VoicePayload.SESSION_DESCRIPTION:
            await self.loadKey(Data)
        elif Operation == VoicePayload.HELLO:
            self.heartbeatInterval = min(Data["heartbeat_interval"] / 1000.0, 5.0)

            if self.keepAliver and not self.keepAliver.done():
                self.keepAliver.cancel()

            self.keepAliver = self.loop.create_task(self.handleHeartbeat())

    async def createConnection(self, data):
        self.client.ssrc = data["ssrc"]
        self.client.endpointIp = data["ip"]
        self.client.endpointPort = data["port"]

        packet = bytearray(70)
        struct.pack_into(">I", packet, 0, data["ssrc"])

        self.client.socket.sendto(
            packet, (self.client.endpointIp, self.client.endpointPort)
        )
        received = await self.loop.sock_recv(self.client.socket, 70)

        start, end = 4, received.index(0, 4)
        self.client.ip = received[start:end].decode("ascii")
        self.client.port = struct.unpack_from(">H", received, len(received) - 2)[0]

        encryptMode = list(
            filter(
                lambda x: x[0] in data["modes"],
                inspect.getmembers(Cipher, predicate=inspect.isfunction),
            )
        )[0][0]

        await self.select_protocol(self.client.ip, self.client.port, encryptMode)

    async def loadKey(self, data):
        self.client.speakState = False

        self.client.encryptMode = data["mode"]
        self.client.secretKey = data.get("secret_key")

    async def poll(self):
        message = await asyncio.wait_for(self.recv(), timeout=30.0)
        await self.messageRecieved(json.loads(message))

    async def close(self, *args, **kwargs):
        if self.keepAliver and not self.keepAliver.done():
            self.keepAliver.cancel()

        await super().close(*args, **kwargs)
