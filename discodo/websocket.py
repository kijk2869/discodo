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
async def feed(request, ws):
    log.info(f'create new websocket connection from {request.socket}.')

    if not hasattr(request.app, 'Nodes'):
        request.app.Nodes = {}
    _Node = None

    async def sendJson(Data):
        log.debug(f'send to {request.socket}: {Data}')
        return await ws.send(json.dumps(Data))

    async def initial_connection():
        payload = {
            'op': 'INITIAL_CONNECTION',
            'd': {
                'ID': ID,
                'REGION': REGION,
                'HEARTBEAT_INTERVAL': WEBSOCKETTIMEOUT / 4
            }
        }

        await sendJson(payload)

    async def authentication_failed():
        payload = {
            'op': 'AUTHENTICATION_FAILED',
            'd': 'Password mismatch.'
        }

        await sendJson(payload)
    
    async def discodoEvent(guild_id, event, *args, **kwargs):
        payload = {
            'op': event,
            'guild_id': guild_id,
            'd': kwargs
        }

        await sendJson(payload)
    
    async def identify(Data):
        if Data['user_id'] in request.app.Nodes:
            payload = {
                'op': 'IDENTIFIED',
                'd': 'Node already initialized.'
            }
        else:
            request.app.Nodes[Data['user_id']] = Node(user_id=Data['user_id'], session_id=Data.get('session_id'))
            request.app.Nodes[Data['user_id']].event.onAny(discodoEvent)
            
            payload = {
                'op': 'IDENTIFIED',
                'd': 'Node initialized.'
            }
        _Node = request.app.Nodes[Data['user_id']]
        await sendJson(payload)
    
    async def heartbeat(Data):
        payload = {
            'op': 'HEARTBEAT_ACK',
            'd': Data
        }

        await sendJson(payload)

    async def discord_event(Data):
        if _Node:
            _Node.discordDispatch(Data)

    if request.headers.get('Authorization') != PASSWORD:
        log.warning(f'websocket connection from {request.socket} password mismatch.')
        await authentication_failed()
        await ws.close(4004)

    await initial_connection()

    while True:
        try:
            Data = json.loads(await asyncio.wait_for(ws.recv(), timeout=WEBSOCKETTIMEOUT))
        except (ConnectionClosed, asyncio.TimeoutError):
            log.info(f'connection from {request.socket} error, closing..')

            await ws.close(4000)

        Operation, Data = Data['op'], Data['d']
        log.debug(f'recieve from {request.socket}: {Operation} - {Data}')

        if Operation == 'IDENTIFY':
            await identify(Data)
        if Operation == 'HEARTBEAT':
            await heartbeat(Data)
        if Operation == 'DISCORD_EVENT':
            await discord_event(Data)