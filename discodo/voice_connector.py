import asyncio
import logging
import re
import socket
import struct
import threading
import uuid

from websockets.exceptions import ConnectionClosed

from .config import Config
from .gateway import VoiceSocket
from .natives import Encrypter, opus

log = logging.getLogger("discodo.VoiceConnector")


class VoiceConnector:
    def __init__(self, manager, data: dict = {}) -> None:
        self.loop = manager.loop

        self.ws = self.socket = None

        self.id = uuid.uuid4()
        self.manager = manager

        self.data = data
        self.guild_id = data.get("guild_id")
        self.channel_id = None

        self._connected = asyncio.Event()
        self._connectedThread = threading.Event()

        self._polling = None
        self._sequence = self._timestamp = 0
        self.encoder = opus.Encoder()

        if data:
            self.loop.create_task(self.createSocket())

    def __del__(self) -> None:
        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        if self.ws:
            self.loop.create_task(self.ws.close(4000))

        if self._polling:
            self._polling.cancel()

    @property
    def user_id(self) -> int:
        return self.manager.id

    @property
    def session_id(self) -> str:
        return self.manager.session_id

    @property
    def sequence(self) -> int:
        return self._sequence

    @sequence.setter
    def sequence(self, value: int) -> None:
        if self._sequence + value > 65535:
            self._sequence = 0
        else:
            self._sequence = value

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: int) -> None:
        if self._timestamp + value > 4294967295:
            self._timestamp = 0
        else:
            self._timestamp = value

    async def createSocket(self, data: dict = None) -> None:
        self._connected.clear()
        self._connectedThread.clear()

        if data:
            self.data = data

        self.guild_id = self.data.get("guild_id")

        self.token = self.data.get("token")
        self.endpoint = re.sub(r"(:[0-9]+)", "", self.data.get("endpoint"))
        log.info(f"voice endpoint {self.endpoint} detected.")

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)

        if self.ws:
            await self.ws.close(4000)

        if hasattr(self, "secretKey"):
            del self.secretKey

        self.ws = await VoiceSocket.connect(self)
        while not hasattr(self, "secretKey"):
            await self.ws.poll()

        if not self._polling or self._polling.done():
            self._polling = self.loop.create_task(self.pollingWS())

        self._connected.set()
        self._connectedThread.set()

    async def pollingWS(self) -> None:
        while True:
            try:
                await self.ws.poll()
            except (asyncio.TimeoutError, ConnectionClosed) as e:
                self._connected.clear()
                self._connectedThread.clear()

                reason = (
                    f"with {e.code}"
                    if isinstance(e, ConnectionClosed)
                    else "because timed out."
                )

                log.info(
                    f"voice connection of {self.guild_id} destroyed {reason}. wait for events."
                )

                try:
                    await asyncio.wait_for(
                        self._connected.wait(), timeout=Config.VCTIMEOUT
                    )
                except asyncio.TimeoutError:
                    return self.__del__()

    def makePacket(self, data: bytes) -> bytes:
        header = bytearray(12)
        header[0], header[1] = 0x80, 0x78

        struct.pack_into(">H", header, 2, self.sequence)
        struct.pack_into(">I", header, 4, self.timestamp)
        struct.pack_into(">I", header, 8, self.ssrc)

        return getattr(Encrypter, self.encryptMode)(self.secretKey, header, data)

    def send(self, data: bytes, encode: bool = True) -> None:
        self.sequence += 1
        if encode:
            data = self.encoder.encode(data)

        Packet = self.makePacket(data)

        self.socket.sendto(Packet, (self.endpointIP, self.endpointPORT))
        self.timestamp += Config.SAMPLES_PER_FRAME
