import json
import os
from functools import wraps

from sanic import Sanic, response
from sanic.exceptions import abort

from ...AudioSource import AudioData
from ...planner import IPRotator
from ...stat import getStat
from .websocket import app as WebsocketBlueprint

app = Sanic(__name__)


@app.listener("before_server_start")
async def applyVariables(app, loop):
    app.PASSWORD = os.getenv("PASSWORD", "hellodiscodo")

    USABLE_IP = json.loads(os.getenv("USABLE_IP", "[]"))

    app.planner = IPRotator() if USABLE_IP else None
    for IP in USABLE_IP if USABLE_IP else []:
        app.planner.add(IP)


app.register_blueprint(WebsocketBlueprint)


def authorized(func):
    def wrapper(request, *args, **kwargs):
        if request.headers.get("Authorization") != app.PASSWORD:
            abort(403, "Password mismatch.")

        return func(request, *args, **kwargs)

    return wrapper


@app.route("/stat")
async def stat(request):
    return response.json(getStat())


@app.route("/getSong")
@authorized
async def getSong(request):
    query = "".join(request.args.get("query", [])).strip()

    if not query:
        abort(400, "Missing parameter query.")

    return response.json(await AudioData.create(query, app.planner))
