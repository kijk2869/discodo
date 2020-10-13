from typing import Coroutine

from sanic import Sanic, response
from sanic.exceptions import abort

from .. import __version__
from ..config import Config
from ..status import getStatus
from .planner import app as PlannerBlueprint
from .restful import app as RestfulBlueprint
from .websocket import app as WebsocketBlueprint

app = Sanic(__name__)

app.register_blueprint(WebsocketBlueprint)
app.register_blueprint(PlannerBlueprint)
app.register_blueprint(RestfulBlueprint)


def authorized(func: Coroutine) -> Coroutine:
    def wrapper(request, *args, **kwargs) -> Coroutine:
        if request.headers.get("Authorization") != Config.PASSWORD:
            abort(403, "Password mismatch.")

        return func(*args, **kwargs)

    return wrapper


@app.route("/")
async def index(request) -> response:
    return response.html(f"<h1>Discodo</h1> <h3>{__version__}")


@app.get("/status")
async def status(request) -> response:
    return response.json(getStatus())
