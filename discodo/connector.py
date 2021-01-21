import asyncio
import logging
import re
import socket
import struct
import threading
import uuid

from .config import Config
from .errors import WebsocketConnectionClosed
from .gateway import VoiceSocket
from .natives import Cipher, opus

log = logging.getLogger("discodo.VoiceConnector")


class VoiceConnector:
    def __init__(self, manager, data: dict = {}) -> None:
        self.loop = manager.loop

        self.ws = self.socket = None

        self.id = str(uuid.uuid4())
        self.manager = manager

        self.data = data
        self.guild_id = data.get("guild_id")
        self._channel_id = None

        self.connectedEvent = asyncio.Event()
        self.connectedThreadEvent = threading.Event()

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

    def __repr__(self) -> str:
        return f"<VoiceConnector guild_id={self.guild_id} connected={self._connected.is_set()} sequence={self.sequence} timestamp={self.timestamp}>"

    @property
    def channel_id(self) -> int:
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value: int) -> int:
        self._channel_id: int = int(value)

    @property
    def user_id(self) -> int:
        """
        User id which is connected.

        :getter: Returns User id
        :rtype: int
        """

        return self.manager.id

    @property
    def session_id(self) -> str:
        """
        Session id which is connected.

        :getter: Returns Session id
        :rtype: str
        """

        return self.manager.session_id

    @property
    def sequence(self) -> int:
        """
        Sequence value which is used to send voice packet.

        :getter: Returns sequence
        :setter: Sets sequence value (max 65535)
        :rtype: int
        """

        return self._sequence

    @sequence.setter
    def sequence(self, value: int) -> None:
        if self._sequence + value > 65535:
            self._sequence = 0
        else:
            self._sequence = value

    @property
    def timestamp(self) -> int:
        """
        Timestamp value which is used to send voice packet.

        :getter: Returns timestamp
        :setter: Sets timestamp value (max 4294967295)
        :rtype: int
        """

        return self._timestamp

    @timestamp.setter
    def timestamp(self, value: int) -> None:
        if self._timestamp + value > 4294967295:
            self._timestamp = 0
        else:
            self._timestamp = value

    async def createSocket(self, data: dict = None) -> None:
        """
        Create UDP socket with discord to send voice packet.

        :param dict data: A VOICE_SERVER_UPDATE payload, defaults to None
        :rtype: None
        """

        self.connectedEvent.clear()
        self.connectedThreadEvent.clear()

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

        self.connectedEvent.set()
        self.connectedThreadEvent.set()

    async def pollingWS(self) -> None:
        while True:
            try:
                await self.ws.poll()
            except (asyncio.TimeoutError, WebsocketConnectionClosed) as e:
                self.connectedEvent.clear()
                self.connectedThreadEvent.clear()

                reason = (
                    f"with {e.code}"
                    if isinstance(e, WebsocketConnectionClosed)
                    else "because timed out."
                )

                log.info(
                    f"voice connection of {self.guild_id} destroyed {reason}. wait for events."
                )

                try:
                    await asyncio.wait_for(
                        self.connectedEvent.wait(), timeout=Config.VCTIMEOUT
                    )
                except asyncio.TimeoutError:
                    return self.__del__()

    def makePacket(self, data: bytes) -> bytes:
        """
        Converts and encrypts data to format.

        :param bytes data: A packet to be converted
        :rtype: bytes
        """

        header = bytearray(12)
        header[0], header[1] = 0x80, 0x78

        struct.pack_into(">H", header, 2, self.sequence)
        struct.pack_into(">I", header, 4, self.timestamp)
        struct.pack_into(">I", header, 8, self.ssrc)

        return getattr(Cipher, self.encryptMode)(self.secretKey, header, data)

    def send(self, data: bytes, encode: bool = True) -> None:
        """
        Send packet to discord.

        :param bytes data: A packet to be sent
        :param bool encode: Whether data is encoded
        :rtype: None
        """

        self.sequence += 1
        if encode:
            data = self.encoder.encode(data)

        Packet = self.makePacket(data)

        self.socket.sendto(Packet, (self.endpointIp, self.endpointPort))
        self.timestamp += Config.SAMPLES_PER_FRAME
