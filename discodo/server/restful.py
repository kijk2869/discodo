from typing import Coroutine

from sanic import Blueprint, response
from sanic.exceptions import abort

from ..config import Config
from ..source import AudioData

app = Blueprint(__name__)


def authorized(func: Coroutine) -> Coroutine:
    def wrapper(request, *args, **kwargs) -> Coroutine:
        if request.headers.get("Authorization") != Config.PASSWORD:
            abort(403, "Password mismatch.")

        return func(*args, **kwargs)

    return wrapper


@app.get("/getSource")
@authorized
async def getSource(request) -> response:
    Query = "".join(request.args.get("query", [])).strip()
    if not Query:
        abort(400, "Missing parameter query.")

    return response.json(await AudioData.create(Query))