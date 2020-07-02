import os
import json
import asyncio
from .node import Node
from sanic import Blueprint
from websockets.exceptions import ConnectionClosed
from logging import getLogger

log = getLogger('discodo.server')

ID = os.getenv('ID')
REGION = os.getenv('REGION')
PASSWORD = os.getenv('PASSWORD')
WEBSOCKETTIMEOUT = os.getenv('WEBSOCKETTIMEOUT', 60.0)

app = Blueprint(__name__)


@app.websocket('/')
async def feedStarter(request, ws):
    Event = asyncio.Event()
    Future = request.app.loop.create_task(WebsocketFeeder().feed(request, ws, Event))
    await Event.wait()

class WebsocketFeeder:
    def __init__(self):
        self._Node = None
        self.request = None
        self.ws = None

    async def sendJson(self, Data):
        log.debug(f'send to {self.request.socket}: {Data}')
        return await self.ws.send(json.dumps(Data))
            
    async def initial_connection(self):
        payload = {
            'op': 'INITIAL_CONNECTION',
            'd': {
                'ID': ID,
                'REGION': REGION,
                'HEARTBEAT_INTERVAL': WEBSOCKETTIMEOUT / 4
            }
        }

        await self.sendJson(payload)
    
    async def authentication_failed(self):
        payload = {
            'op': 'AUTHENTICATION_FAILED',
            'd': 'Password mismatch.'
        }

        await self.sendJson(payload)
    
    async def discodoEvent(self, guild_id, event, *args, **kwargs):
        payload = {
            'op': event,
            'guild_id': guild_id,
            'd': kwargs
        }

        await self.sendJson(payload)
    
    async def identify(self, Data):
        if Data['user_id'] in self.request.app.Nodes:
            payload = {
                'op': 'IDENTIFIED',
                'd': 'Node already initialized.'
            }
        else:
            self.request.app.Nodes[Data['user_id']] = Node(
                user_id=Data['user_id'], session_id=Data.get('session_id'))
            self.request.app.Nodes[Data['user_id']].event.onAny(self.discodoEvent)

            payload = {
                'op': 'IDENTIFIED',
                'd': 'Node initialized.'
            }
        self._Node = self.request.app.Nodes[Data['user_id']]
        await self.sendJson(payload)
    
    async def heartbeat(self, Data):
        payload = {
            'op': 'HEARTBEAT_ACK',
            'd': Data
        }

        await self.sendJson(payload)
    
    async def discord_event(self, Data):
        if self._Node:
            self._Node.discordDispatch(Data)

    async def feed(self, request, ws, _Event):
        log.info(f'create new websocket connection from {request.socket}.')

        self.request, self.ws = request, ws

        if not hasattr(request.app, 'Nodes'):
            request.app.Nodes = {}

        if request.headers.get('Authorization') != PASSWORD:
            log.warning(f'websocket connection from {request.socket} password mismatch.')
            await self.authentication_failed()

            return await ws.close(4004)

        await self.initial_connection()

        while True:
            try:
                JSONData = json.loads(await asyncio.wait_for(ws.recv(), timeout=WEBSOCKETTIMEOUT))
            except (ConnectionClosed, asyncio.TimeoutError):
                log.info(f'connection from {request.socket} error, closing..')

                if self._Node:
                    del request.app.Nodes[self._Node.user_id]
                    self._Node = None

                return await ws.close(4000)

            Operation, Data = JSONData['op'], JSONData['d']
            log.debug(f'recieve from {request.socket}: {Operation} - {Data}')

            if Operation == 'IDENTIFY':
                await self.identify(Data)
            if Operation == 'HEARTBEAT':
                await self.heartbeat(Data)
            if Operation == 'DISCORD_EVENT':
                await self.discord_event(Data)
