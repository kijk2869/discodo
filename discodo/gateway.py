import asyncio
import concurrent.futures
import json
import logging
import struct
import threading
import time
from collections import deque

import websockets

from .natives import Encrypter

log = logging.getLogger("discodo.gateway")


class keepAlive(threading.Thread):
    def __init__(self, ws, interval: int, *args, **kwargs) -> None:
        threading.Thread.__init__(self, *args, **kwargs)
        self.daemon = True

        self.ws = ws
        self.interval = interval
        self.Stopped = threading.Event()
        self.latency = None
        self.recent_latencies = deque(maxlen=20)

        self._lastAck = self._lastSend = time.perf_counter()
        self.timeout = ws.heartbeatTimeout
        self.threadId = ws.threadId

    def run(self) -> None:
        while not self.Stopped.wait(self.interval):
            if (self._lastAck + self.timeout) < time.perf_counter():
                Runner = asyncio.run_coroutine_threadsafe(
                    self.ws.close(4000), self.ws.loop
                )

                try:
                    Runner.result()
                except:
                    pass
                finally:
                    return self.stop()

            payload = {"op": self.ws.HEARTBEAT, "d": int(time.time() * 1000)}
            Runner = asyncio.run_coroutine_threadsafe(
                self.ws.sendJson(payload), self.ws.loop
            )
            try:
                totalBlocked = 0
                while True:
                    try:
                        Runner.result(10)
                        break
                    except concurrent.futures.TimeoutError:
                        totalBlocked += 10
                        log.warning(
                            f"Heartbeat blocked for more than {totalBlocked} seconds."
                        )
            except:
                return self.stop()
            else:
                self._lastSend = time.perf_counter()

    def ack(self) -> None:
        self._lastAck = time.perf_counter()
        self.latency = self._lastAck - self._lastSend
        self.recent_latencies.append(self.latency)

    def stop(self) -> None:
        self.Stopped.set()


class VoiceSocket(websockets.client.WebSocketClientProtocol):
    IDENTIFY = 0
    SELECT_PROTOCOL = 1
    READY = 2
    HEARTBEAT = 3
    SESSION_DESCRIPTION = 4
    SPEAKING = 5
    HEARTBEAT_ACK = 6
    RESUME = 7
    HELLO = 8
    RESUMED = 9
    CLIENT_DISCONNECT = 13

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    @classmethod
    async def connect(cls, client, resume=False):
        ws = await websockets.connect(
            f"wss://{client.endpoint}/?v=4",
            loop=client.loop,
            klass=cls,
            compression=None,
        )
        ws.client = client

        ws._keepAliver = None
        ws.heartbeatTimeout = 60.0
        ws.threadId = threading.get_ident()

        if not resume:
            await ws.identify()
        else:
            await ws.resume()

        return ws

    @property
    def latency(self) -> float:
        return self._keepAliver.latency if self._keepAliver else None

    @property
    def averageLatency(self) -> float:
        if not self._keepAliver:
            return None

        return sum(self._keepAliver.recent_latencies) / len(
            self._keepAliver.recent_latencies
        )

    async def sendJson(self, data: dict) -> None:
        log.debug(f"send to websocket {data}")
        await self.send(json.dumps(data))

    async def identify(self) -> None:
        payload = {
            "op": self.IDENTIFY,
            "d": {
                "server_id": str(self.client.guild_id),
                "user_id": str(self.client.user_id),
                "session_id": self.client.session_id,
                "token": self.client.token,
            },
        }
        await self.sendJson(payload)

    async def resume(self) -> None:
        payload = {
            "op": self.RESUME,
            "d": {
                "server_id": str(self.client.guild_id),
                "user_id": str(self.client.user_id),
                "session_id": self.client.session_id,
                "token": self.client.token,
            },
        }
        await self.sendJson(payload)

    async def select_protocol(self, ip: str, port: str, mode: str) -> None:
        payload = {
            "op": self.SELECT_PROTOCOL,
            "d": {
                "protocol": "udp",
                "data": {"address": ip, "port": port, "mode": mode},
            },
        }
        await self.sendJson(payload)

    async def speak(self, state: bool = True) -> None:
        self.client.speakState = state

        payload = {"op": self.SPEAKING, "d": {"speaking": int(state), "delay": 0}}
        await self.sendJson(payload)

    async def receive(self, message: dict) -> None:
        Operation, Data = message["op"], message.get("d")
        log.debug(f"websocket recieved {Operation}: {Data}")

        if Operation == self.READY:
            await self.createConnection(Data)
        elif Operation == self.HEARTBEAT_ACK:
            self._keepAliver.ack()
        elif Operation == self.SESSION_DESCRIPTION:
            await self.loadKey(Data)
        elif Operation == self.HELLO:
            interval = Data["heartbeat_interval"] / 1000.0
            self._keepAliver = keepAlive(self, min(interval, 5.0))
            self._keepAliver.start()

    async def createConnection(self, data: dict) -> None:
        self.client.ssrc = data["ssrc"]
        self.client.endpointPORT = data["port"]
        self.client.endpointIP = data["ip"]

        packet = bytearray(70)
        struct.pack_into(">I", packet, 0, data["ssrc"])

        self.client.socket.sendto(
            packet, (self.client.endpointIP, self.client.endpointPORT)
        )
        _recieved = await self.loop.sock_recv(self.client.socket, 70)

        _start, _end = 4, _recieved.index(0, 4)
        self.client.ip = _recieved[_start:_end].decode("ascii")
        self.client.port = struct.unpack_from(">H", _recieved, len(_recieved) - 2)[0]

        encryptModes = [Mode for Mode in data["modes"] if Mode in Encrypter.available]
        log.debug(f'recieved encrypt modes {data["modes"]}')

        encryptMode = encryptModes[0]
        log.info(f"select encrypt mode {encryptMode}")

        await self.select_protocol(self.client.ip, self.client.port, encryptMode)

    async def loadKey(self, data: dict) -> None:
        log.info("recieved voice secret key.")

        await self.speak(True)
        await self.speak(False)

        self.client.encryptMode = data["mode"]
        self.client.secretKey = data.get("secret_key")

    async def poll(self) -> None:
        Message = await asyncio.wait_for(self.recv(), timeout=30.0)
        await self.receive(json.loads(Message))

    async def close(self, *args, **kwargs) -> None:
        if self._keepAliver:
            self._keepAliver.stop()

        await super().close(*args, **kwargs)
