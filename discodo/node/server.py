from sanic import Sanic

app = Sanic(__name__)

from .websocket import app as WebsocketBlueprint
app.register_blueprint(WebsocketBlueprint)

if __name__ == '__main__':
    app.run()