import asyncio
import concurrent.futures
import json
import threading
import time
from collections import deque
from logging import getLogger

import websockets

log = getLogger("discodo.client")


class keepAlive(threading.Thread):
    def __init__(self, ws, interval: int, *args, **kwargs):
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

    def run(self):
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

    def ack(self):
        self._lastAck = time.perf_counter()
        self.latency = self._lastAck - self._lastSend
        self.recent_latencies.append(self.latency)

    def stop(self):
        self.Stopped.set()


class NodeConnection(websockets.client.WebSocketClientProtocol):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    async def connect(cls, client, loop=asyncio.get_event_loop()):
        ws = await websockets.connect(
            client.URL,
            loop=loop,
            klass=cls,
            extra_headers={"Authorization": client.password},
        )

        ws.client = client
        ws.heartbeatTimeout = 60.0
        ws.threadId = threading.get_ident()

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

    async def sendJson(self, data):
        log.debug(f"send to websocket {data}")
        await super().send(json.dumps(data))

    async def send(self, Operation, Data):
        payload = {"op": Operation, "d": Data}

        await self.sendJson(payload)

    async def poll(self):
        try:
            Message = await asyncio.wait_for(self.recv(), timeout=30.0)
            JsonData = json.loads(Message)
        except websockets.exceptions.ConnectionClosed as exc:
            raise exc
        else:
            Operation, Data = JsonData["op"], JsonData["d"]

            if Operation == "HELLO":
                await self.HELLO(Data)
            elif Operation == "HEARTBEAT_ACK":
                await self.HEARTBEAT_ACK(Data)

            return Operation, Data

    async def close(self, *args, **kwargs):
        if self._keepAliver:
            self._keepAliver.stop()

        await super().close(*args, **kwargs)

    async def HELLO(self, Data):
        self._keepAliver = keepAlive(self, min(Data["heartbeat_interval"], 5.0))
        self._keepAliver.start()

    async def HEARTBEAT_ACK(self, Data):
        self._keepAliver.ack()
