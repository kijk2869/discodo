from websocket import app as WebsocketBlueprint
from sanic import Sanic
import logging
logging.basicConfig(level=logging.DEBUG)

app = Sanic(__name__)

app.register_blueprint(WebsocketBlueprint)

app.run('0.0.0.0', port=80, debug=True)
