import asyncio
import concurrent.futures
import json
import logging
import threading
import time
import warnings
from collections import deque
from typing import Any

import aiohttp

from .. import __version__
from ..errors import WebsocketConnectionClosed

log = logging.getLogger("discodo.client")


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

                self.stop()
                return

            payload = {"op": "HEARTBEAT", "d": int(time.time() * 1000)}
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


class NodeConnection:
    def __init__(self, Node, session, socket) -> None:
        self.Node = Node
        self.session = session
        self.socket = socket
        self.loop = Node.loop

        self.closeCode = None

        self.keepAliver = None
        self.heartbeatTimeout = 60.0
        self.threadId = threading.get_ident()

    def __del__(self) -> None:
        self.loop.call_soon_threadsafe(lambda: self.loop.create_task(self.close()))

    @classmethod
    async def connect(cls, node):
        session = aiohttp.ClientSession()

        try:
            socket = await session.ws_connect(
                node.WS_URL,
                max_msg_size=0,
                timeout=60.0,
                autoclose=False,
                headers={"Authorization": node.password},
            )
        except Exception as e:
            await session.close()
            raise e

        return cls(node, session, socket)

    @property
    def is_connected(self) -> bool:
        return not self.socket.closed

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

    async def sendJson(self, data) -> None:
        log.debug(f"send to websocket {data}")
        await self.socket.send_json(data)

    async def send(self, Operation: dict, Data: Any = None) -> None:
        payload = {"op": Operation, "d": Data}

        await self.sendJson(payload)

    async def poll(self) -> None:
        message = await asyncio.wait_for(self.socket.receive(), timeout=30.0)

        if message.type is aiohttp.WSMsgType.TEXT:
            JsonData = json.loads(message.data)

            Operation, Data = JsonData["op"], JsonData["d"]

            if Operation == "HELLO":
                await self.HELLO(Data)
            elif Operation == "HEARTBEAT_ACK":
                await self.HEARTBEAT_ACK(Data)

            return Operation, Data
        elif message.type is aiohttp.WSMsgType.ERROR:
            raise WebsocketConnectionClosed(self.socket) from message.data
        elif message.type in (
            aiohttp.WSMsgType.CLOSED,
            aiohttp.WSMsgType.CLOSE,
            aiohttp.WSMsgType.CLOSING,
        ):
            raise WebsocketConnectionClosed(self.socket, code=self.socket.close_code)

    async def close(self, code: int = 1000) -> None:
        if self.keepAliver:
            self.keepAliver.stop()

        self._close_code = code
        await self.socket.close(code=code)
        await self.session.close()

    async def HELLO(self, Data: dict) -> None:
        if Data.get("version") != __version__:
            warnings.warn(
                f"Discodo version mismatch between server and client. (Node {Data.get('version')}/Client {__version__})",
                UserWarning,
            )

        self._keepAliver = keepAlive(self, min(Data["heartbeat_interval"], 5.0))
        self._keepAliver.start()

    async def HEARTBEAT_ACK(self, Data: dict) -> None:
        self._keepAliver.ack()
