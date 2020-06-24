import socket
import asyncio
from .gateway import VoiceSocket

class VoiceClient:
    def __init__(self, client, guild_id, data):
        self.loop = asyncio.get_event_loop()
        self.ws = None
        self.socket = None

        self.client = client
        self.guild_id = guild_id
        self.user_id = self.client.user_id

        self.data = data
        self.session_id = self.client.session_id

        self._polling = None
        self.loop.create_task(self.createSocket())


    async def createSocket(self, data: dict=None):
        if data:
            self.data = data
        print(self.data)
        self.token = self.data.get('token')
        endpoint = self.data.get('endpoint')
        self.endpoint = endpoint.replace(':80', '')
        self.endpointIp = socket.gethostbyname(self.endpoint)

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking(False)

        self.ws = await VoiceSocket.connect(self)
        while not hasattr(self, 'secretKey'):
            await self.ws.poll()
        
        if not self._polling:
            self._polling = self.loop.create_task(self.pollingWs())
    
    async def pollingWs(self):
        while True:
            await self.ws.poll()