import os
import socket
import struct
import asyncio
from logging import getLogger
from .gateway import VoiceSocket
from .encrypt import getEncryptModes
from .natives import opus

SAMPLING_RATE = os.getenv('SAMPLING_RATE', 48000)
FRAME_LENGTH = os.getenv('FRAME_LENGTH', 20)
SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)

log = getLogger('discodo.VoiceClient')


class VoiceClient:
    def __init__(self, client, data):
        self.loop = asyncio.get_event_loop()
        self.ws = None
        self.socket = None

        self.client = client
        self.user_id = self.client.user_id

        self.data = data
        self.session_id = self.client.session_id
        self.guild_id = self.data.get('guild_id')

        self._sequence = 0
        self._timestamp = 0

        self._polling = None
        self.encoder = opus.Encoder()
        self.loop.create_task(self.createSocket())

    @property
    def sequence(self):
        return self._sequence

    @sequence.setter
    def sequence(self, value):
        if self._sequence + value > 65535:
            self._sequence = 0
        else:
            self._sequence = value

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, value):
        if self._timestamp + value > 4294967295:
            self._timestamp = 0
        else:
            self._timestamp = value

    async def createSocket(self, data: dict = None):
        if data:
            self.data = data
            
        self.guild_id = self.data.get('guild_id')

        self.token = self.data.get('token')
        endpoint = self.data.get('endpoint')
        self.endpoint = endpoint.replace(':80', '')
        self.endpointIp = socket.gethostbyname(self.endpoint)
        log.info(f'voice endpoint {self.endpoint} ({self.endpointIp}) detected.')

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)

        if self.ws:
            await self.ws.close(4000)

        self.ws = await VoiceSocket.connect(self)
        while not hasattr(self, 'secretKey'):
            await self.ws.poll()

        if not self._polling or self._polling.done():
            self._polling = self.loop.create_task(self.pollingWs())

    async def pollingWs(self):
        while True:
            await self.ws.poll()

    def makePacket(self, data):
        header = bytearray(12)
        header[0] = 0x80
        header[1] = 0x78

        struct.pack_into('>H', header, 2, self.sequence)
        struct.pack_into('>I', header, 4, self.timestamp)
        struct.pack_into('>I', header, 8, self.ssrc)

        encryptPacket = getEncryptModes()[self.encryptMode]
        return encryptPacket(self.secretKey, header, data)

    def send(self, data, encode=True):
        self.sequence += 1
        if encode:
            data = self.encoder.encode(data)

        Packet = self.makePacket(data)

        self.socket.sendto(Packet, (self.endpointIp, self.endpointPort))
        self.timestamp += SAMPLES_PER_FRAME
