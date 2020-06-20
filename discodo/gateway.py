import json
import asyncio
import websockets

class VoiceSocket(websockets.client.WebSocketClientProtocol):
    IDENTIFY            = 0
    SELECT_PROTOCOL     = 1
    READY               = 2
    HEARTBEAT           = 3
    SESSION_DESCRIPTION = 4
    SPEAKING            = 5
    HEARTBEAT_ACK       = 6
    RESUME              = 7
    HELLO               = 8
    INVALIDATE_SESSION  = 9
    CLIENT_CONNECT      = 12
    CLIENT_DISCONNECT   = 13

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @classmethod
    async def connect(cls, client, loop=asyncio.get_event_loop(), resume=False):
        ws = await websockets.connect(f'wss://{client.endpoint}/?v=4', loop=loop, klass=cls, compression=None)
        ws.client = client

        if not resume:
            await ws.identify()
        else:
            await ws.resume()

        return ws
    
    async def sendJson(self, data):
        await self.send(json.dumps(data))

    async def identify(self):
        payload = {
            'op': self.IDENTIFY,
            'd': {
                'server_id': str(self.client.server_id),
                'user_id': str(self.client.user_id),
                'session_id': self.client.session_id,
                'token': self.client.token
            }
        }
        await self.sendJson(payload)

    async def resume(self):
        payload = {
            'op': self.RESUME,
            'd': {
                'server_id': str(self.client.server_id),
                'user_id': str(self.client.user_id),
                'session_id': self.client.session_id,
                'token': self.client.token
            }
        }
        await self.sendJson(payload)
    
    async def receive(self, message):
        Operation, Data = message['op'], message.get('d')

        if Operation == self.READY:
            pass
        elif Operation == self.HEARTBEAT_ACK:
            pass
        elif Operation == self.INVALIDATE_SESSION:
            pass
        elif Operation == self.SESSION_DESCRIPTION:
            pass
        elif Operation == self.HELLO:
            pass
    
    async def polling(self):
        try:
            Message = await asyncio.wait_for(self.recv(), timeout=30.0)
            await self.receive(json.loads(Message))
        except websockets.exceptions.ConnectionClosed as exc:
            raise websockets.exceptions.ConnectionClosed