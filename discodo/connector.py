import asyncio
import contextlib
import logging
import re
import socket
import struct
import threading
import uuid

import websockets
from websockets.exceptions import ConnectionClosed

from .config import Config
from .enums import WebsocketCloseCode
from .errors import EncryptModeNotReceived
from .gateway import VoiceSocket
from .natives import opus
from .natives.encrypt import Cipher

log = logging.getLogger("discodo.connector")


class VoiceConnector:
    def __init__(self, manager, data=None):
        self.id = str(uuid.uuid4())
        self.loop = manager.loop
        self.manager = manager

        self.ws = self.socket = None

        self.data = data or {}
        self._channel_id = None

        self.encoder = opus.Encoder()
        self.connectedEvent = asyncio.Event()
        self.connectedThreadEvent = threading.Event()

        self._polling = None
        self.endpointIp = self.endpointPort = None
        self._sequence = self._timestamp = self.ssrc = 0
        self.speakState = False
        self.encryptMode = None

        if data:
            self.loop.create_task(self.createSocket())

    def __del__(self):
        if self.socket:
            with contextlib.suppress(Exception):
                self.socket.close()

        if self.ws and not self.ws.closed:
            self.loop.create_task(self.ws.close(4000))

        if self._polling:
            self._polling.cancel()

    def __repr__(self) -> str:
        return f"<VoiceConnector guild_id={self.guild_id} connected={self.connectedEvent.is_set()} sequence={self.sequence} timestamp={self.timestamp}>"

    @property
    def channel_id(self):
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value):
        self._channel_id = str(value)

    @property
    def user_id(self) -> str:
        return self.manager.id

    @property
    def session_id(self) -> str:
        return self.manager.session_id

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, value):
        self._data = value

        self.token = self._data.get("token")
        self.endpoint = (
            re.sub(r"(:[0-9]+)", "", self._data["endpoint"])
            if self._data.get("endpoint")
            else None
        )
        self.guild_id = self._data.get("guild_id")

    @property
    def sequence(self) -> int:
        return self._sequence

    @sequence.setter
    def sequence(self, value: int):
        if self._sequence + value > 65535:
            self._sequence = 0
        else:
            self._sequence = value

    @property
    def timestamp(self) -> int:
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: int):
        if self._timestamp + value > 4294967295:
            self._timestamp = 0
        else:
            self._timestamp = value

    async def createSocket(self, data=None):
        self.connectedEvent.clear()
        self.connectedThreadEvent.clear()

        if data:
            self.data = data

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)

        if self.ws and not self.ws.closed:
            await self.ws.close(4000)

        if hasattr(self, "secretKey"):
            del self.secretKey  # type: ignore

        self.ws = await VoiceSocket.connect(self)
        while not hasattr(self, "secretKey"):
            await self.ws.poll()  # type: ignore

        if not self._polling or self._polling.done():
            self._polling = self.loop.create_task(self.pollingWS())

        self.connectedEvent.set()
        self.connectedThreadEvent.set()

    async def pollingWS(self):
        while True:
            try:
                await self.ws.poll()  # type: ignore
            except (asyncio.TimeoutError, websockets.ConnectionClosed) as e:
                self.connectedEvent.clear()
                self.connectedThreadEvent.clear()

                closeCode = WebsocketCloseCode(
                    e.code if isinstance(e, websockets.ConnectionClosed) else 1000
                )

                reason = (
                    f"with {closeCode.value}: {closeCode.name}"
                    if isinstance(e, ConnectionClosed)
                    else "because timed out."
                )

                (log.warn if closeCode.warn else log.info)(
                    f"voice connection of {self.guild_id} destroyed {reason}, {'resuming...' if closeCode.resume else 'wait for events.'}"
                )

                if closeCode.resume:
                    await self.createSocket()

                try:
                    await asyncio.wait_for(
                        self.connectedEvent.wait(), timeout=Config.VCTIMEOUT
                    )
                except asyncio.TimeoutError:
                    if closeCode.resume:
                        log.warn(
                            f"resuming voice connection of {self.guild_id} timed out."
                        )

                    return self.__del__()
            except asyncio.CancelledError:
                return self.__del__()
            except:
                log.exception(
                    "while polling websocket, an unhandled exception occured."
                )

    def makePacket(self, data: bytes) -> bytes:
        header = bytearray(12)
        header[0], header[1] = 0x80, 0x78

        struct.pack_into(">H", header, 2, self.sequence)
        struct.pack_into(">I", header, 4, self.timestamp)
        struct.pack_into(">I", header, 8, self.ssrc)

        if not self.encryptMode:
            raise EncryptModeNotReceived

        return getattr(Cipher, self.encryptMode)(self.secretKey, header, data)  # type: ignore

    def send(self, data: bytes, encode: bool = True):
        self.sequence += 1
        if encode:
            data = self.encoder.encode(data)

        Packet = self.makePacket(data)

        self.socket.sendto(Packet, (self.endpointIp, self.endpointPort))
        self.timestamp += Config.SAMPLES_PER_FRAME
