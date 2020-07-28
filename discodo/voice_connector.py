import asyncio
import os
import socket
import struct
import threading
from logging import getLogger

from websockets.exceptions import ConnectionClosed

from .encrypt import getEncryptModes
from .gateway import VoiceSocket
from .natives import opus

VCTIMEOUT = float(os.getenv("VCTIMEOUT", "300.0"))
SAMPLING_RATE = int(os.getenv("SAMPLING_RATE", "48000"))
FRAME_LENGTH = int(os.getenv("FRAME_LENGTH", "20"))
SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)

log = getLogger("discodo.VoiceConnector")


class VoiceConnector:
    def __init__(self, client, data):
        self.loop = asyncio.get_event_loop()
        self.ws = None
        self.socket = None

        self.client = client
        self.user_id = self.client.user_id

        self.data = data
        self.session_id = self.client.session_id
        self.guild_id = self.data.get("guild_id")

        self._sequence = 0
        self._timestamp = 0

        self._connected = asyncio.Event()
        self._connectedThread = threading.Event()

        self._polling = None
        self.encoder = opus.Encoder()
        self.loop.create_task(self.createSocket())

    def __del__(self):
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

    async def createSocket(self, data: dict = None):
        self._connected.clear()
        self._connectedThread.clear()

        if data:
            self.data = data

        self.guild_id = self.data.get("guild_id")

        self.token = self.data.get("token")
        endpoint = self.data.get("endpoint")
        self.endpoint = endpoint.replace(":80", "")
        self.endpointIp = socket.gethostbyname(self.endpoint)
        log.info(f"voice endpoint {self.endpoint} ({self.endpointIp}) detected.")

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
            self._polling = self.loop.create_task(self.pollingWs())

        self._connected.set()
        self._connectedThread.set()

    async def pollingWs(self):
        while True:
            try:
                await self.ws.poll()
            except (asyncio.TimeoutError, ConnectionClosed) as e:
                self._connected.clear()
                self._connectedThread.clear()

                if isinstance(e, ConnectionClosed):
                    reason = f"with {e.code}"
                else:
                    reason = "because timed out."

                log.info(
                    f"voice connection of {self.guild_id} destroyed {reason}. wait for events."
                )

                try:
                    await asyncio.wait_for(self._connected.wait(), timeout=VCTIMEOUT)
                except asyncio.TimeoutError:
                    return self.__del__()

    def makePacket(self, data: bytes) -> bytes:
        header = bytearray(12)
        header[0] = 0x80
        header[1] = 0x78

        struct.pack_into(">H", header, 2, self.sequence)
        struct.pack_into(">I", header, 4, self.timestamp)
        struct.pack_into(">I", header, 8, self.ssrc)

        encryptPacket = getEncryptModes()[self.encryptMode]
        return encryptPacket(self.secretKey, header, data)

    def send(self, data: bytes, encode: bool = True):
        self.sequence += 1
        if encode:
            data = self.encoder.encode(data)

        Packet = self.makePacket(data)

        self.socket.sendto(Packet, (self.endpointIp, self.endpointPort))
        self.timestamp += SAMPLES_PER_FRAME
