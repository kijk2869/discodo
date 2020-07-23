import asyncio

from .websocket import app as WebsocketBlueprint
from sanic import Sanic

import logging

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("websockets").setLevel(logging.INFO)

app = Sanic(__name__)

app.register_blueprint(WebsocketBlueprint)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(app.create_server(host='0.0.0.0', return_asyncio_server=True))
    loop.run_forever()
