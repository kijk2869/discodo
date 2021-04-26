from sanic import Sanic, response

from .. import __version__
from ..utils import getStatus
from .planner import app as PlannerBlueprint
from .restful import app as RestfulBlueprint
from .websocket import app as WebsocketBlueprint

app = Sanic(__name__, configure_logging=False)

app.config.KEEP_ALIVE_TIMEOUT = 75
app.config.FALLBACK_ERROR_FORMAT = "json"

app.blueprint(PlannerBlueprint)
app.blueprint(WebsocketBlueprint)
app.blueprint(RestfulBlueprint)


@app.route("/")
async def index(request):
    return response.html(f"<h1>Discodo</h1> <h3>{__version__}")


@app.route("/status")
async def status(request):
    return response.json(getStatus())
