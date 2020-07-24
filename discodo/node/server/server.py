import asyncio

from .websocket import app as WebsocketBlueprint
from sanic import Sanic

app = Sanic(__name__)

app.register_blueprint(WebsocketBlueprint)