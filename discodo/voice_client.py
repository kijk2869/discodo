import socket
import asyncio

class VoiceClient:
    def __init__(self, client, guild_id, data):
        self.loop = asyncio.get_event_loop()
        self.ws = None
        self.socket = None

        self.client = client
        self.guild_id = guild_id

        self.token = data.get('token')
        endpoint = data.get('endpoint')
        self.endpoint = endpoint.replace(':80', '')
        self.endpointIp = socket.gethostbyname(self.endpoint)

    async def createSocket(self):
        self.session_id = self.client.session_id

        if self.socket:
            try:
                self.socket.close()
            except:
                pass

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setblocking = False
