import itertools
from typing import Coroutine

from sanic import Sanic, response
from sanic.exceptions import abort

from .. import __version__
from ..config import Config
from ..status import getStatus
from .dashboard import app as DashboardBlueprint
from .planner import app as PlannerBlueprint
from .restful import app as RestfulBlueprint
from .websocket import app as WebsocketBlueprint

app = Sanic(__name__)

app.blueprint(WebsocketBlueprint)
app.blueprint(PlannerBlueprint)
app.blueprint(RestfulBlueprint)
app.blueprint(DashboardBlueprint)


def authorized(func: Coroutine) -> Coroutine:
    def wrapper(request, *args, **kwargs) -> Coroutine:
        if request.headers.get("Authorization") != Config.PASSWORD:
            abort(403, "Password mismatch.")

        return func(request, *args, **kwargs)

    return wrapper


@app.route("/")
async def index(request) -> response:
    return response.html(f"<h1>Discodo</h1> <h3>{__version__}")


@app.route("/version")
async def version(request) -> response:
    return response.text(__version__)


@app.get("/status")
async def status(request) -> response:
    Data = getStatus()
    if hasattr(app, "ClientManagers"):
        Data["Connections"] = len(app.ClientManagers)
        Data["Players"] = len(
            list(
                itertools.chain.from_iterable(
                    map(lambda x: x.voiceClients, app.ClientManagers.values())
                )
            )
        )
    else:
        Data["Connections"] = Data["Players"] = 0

    return response.json(Data)
