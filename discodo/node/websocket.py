import os
import json
import asyncio
import logging
from sanic import Blueprint
from sanic.websocket import ConnectionClosed
from websockets import exceptions

WSTIMEOUT = float(os.getenv('WSTIMEOUT', '60'))

log = logging.getLogger('discodo.server')

app = Blueprint(__name__)

@app.websocket('/')
async def feed(request, ws):
    handler = WebsocketHandler(request, ws)
    await handler.join()

class WebsocketHandler:
    def __init__(self, request, ws):
        self.loop = asyncio.get_event_loop()
        self.request = request
        self.ws = ws

        self.loop.create_task(self.handle())

        self._running = asyncio.Event()

    async def join(self):
        return await self._running.wait()
    
    async def handle(self):
        if self._running.is_set():
            self._running.clear()
        
        try:
            await self._handle()
        finally:
            self._running.set()
    
    async def _handle(self):
        log.info(f'new websocket connection created from {self.request.ip}.')
        while True:
            try:
                RAWDATA = await asyncio.wait_for(self.ws.recv(), timeout=WSTIMEOUT)
            except (asyncio.TimeoutError, ConnectionClosed) as exception:
                if isinstance(exception, asyncio.TimeoutError):
                    log.info('websocket connection closing because of timeout.')
                elif isinstance(exception, ConnectionClosed):
                    log.info(f'websocket connection disconnected. code {exception.code}')
                
                # have to cleanup
                return
            
            Data = json.loads(RAWDATA)