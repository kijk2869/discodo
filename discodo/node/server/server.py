import asyncio

from sanic import Sanic

from .websocket import app as WebsocketBlueprint

app = Sanic(__name__)

app.register_blueprint(WebsocketBlueprint)