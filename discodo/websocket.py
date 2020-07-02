import os
import json
import asyncio
from sanic import Blueprint
from websockets.exceptions import ConnectionClosed
from logging import getLogger

log = getLogger('discodo.server')

ID = os.getenv('ID')
REGION = os.getenv('REGION')
PASSWORD = os.getenv('PASSWORD')
WEBSOCKETTIMEOUT = os.getenv('WEBSOCKETTIMEOUT', 60.0)

app = Blueprint(__name__)

async def sendJson(ws, Data):
    return await ws.send(json.dumps(Data))

@app.websocket('/')
async def feed(request, ws):
    log.info(f'create new websocket connection from {request.socket}.')
    if request.headers.get('Authorization') != PASSWORD:
        log.warning(f'websocket connection from {request.socket} password mismatch.')
        await authentication_failed(ws)
        await ws.close(4004)

    await initial_connection(ws)

    while True:
        try:
            Data = await asyncio.wait_for(ws.recv(), timeout=WEBSOCKETTIMEOUT)
        except (ConnectionClosed, asyncio.TimeoutError):
            log.info(f'connection from {request.socket} error, closing..')

            await ws.close()

        print(Data)

async def initial_connection(ws):
    payload = {
        'op': 'INITIAL_CONNECTION',
        'd': {
            'ID': ID,
            'REGION': REGION,
            'HEARTBEAT_INTERVAL': WEBSOCKETTIMEOUT / 4
        }
    }

    await sendJson(ws, payload)

async def authentication_failed(ws):
    payload = {
        'op': 'AUTHENTICATION_FAILED',
        'd': 'Password mismatch.'
    }

    await sendJson(ws, payload)