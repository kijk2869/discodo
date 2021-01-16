import json
from typing import Coroutine

from sanic import Blueprint, response
from sanic.exceptions import abort

from ..config import Config
from ..extractor import search
from ..source import AudioData

app = Blueprint(__name__)


def authorized(func: Coroutine) -> Coroutine:
    def wrapper(request, *args, **kwargs) -> Coroutine:
        if request.headers.get("Authorization") != Config.PASSWORD:
            abort(403, "Password mismatch.")

        return func(request, *args, **kwargs)

    return wrapper


def need_manager(func: Coroutine) -> Coroutine:
    def wrapper(request, *args, **kwargs):
        user_id = int(request.headers.get("User-ID"))

        if (
            not hasattr(request.app, "ClientManagers")
            or not user_id in request.app.ClientManagers
        ):
            abort(404, "ClientManager not found.")

        manager = request.app.ClientManagers[user_id]

        return func(request, manager, *args, **kwargs)

    return wrapper


def need_voiceclient(func: Coroutine) -> Coroutine:
    def wrapper(request, *args, **kwargs):
        user_id = int(request.headers.get("User-ID"))

        if (
            not hasattr(request.app, "ClientManagers")
            or not user_id in request.app.ClientManagers
        ):
            abort(404, "ClientManager not found.")

        manager = request.app.ClientManagers[user_id]

        guild_id = int(request.headers.get("Guild-ID"))

        VoiceClient = manager.getVC(guild_id, safe=True)

        VoiceClientID = request.headers.get("VoiceClient-ID")

        if not VoiceClient:
            abort(404, "VoiceClient not found.")

        if VoiceClientID != VoiceClient.id:
            abort(403, "VoiceClient ID mismtach.")

        return func(request, VoiceClient, *args, **kwargs)

    return wrapper


class Encoder(json.JSONEncoder):
    def default(self, o):
        return o.__dict__()


def JSONResponse(
    body,
    status=200,
    headers=None,
    content_type="application/json",
    **kwargs,
):
    return response.HTTPResponse(
        json.dumps(body, **kwargs, cls=Encoder),
        headers=headers,
        status=status,
        content_type=content_type,
    )


@app.get("/getContext")
@authorized
@need_manager
async def getContext(request, manager) -> JSONResponse:
    return JSONResponse({"context": manager.Context})


@app.get("/setContext")
@authorized
@need_manager
async def setContext(request, manager) -> JSONResponse:
    if "context" not in request.json:
        abort(400, "Bad data `context`")

    manager.Context.update(request.json["context"])

    return JSONResponse({"context": manager.Context})


@app.get("/getVCContext")
@authorized
@need_voiceclient
async def getVCContext(request, VoiceClient) -> JSONResponse:
    return JSONResponse({"context": VoiceClient.Context})


@app.get("/setVCContext")
@authorized
@need_voiceclient
async def setVCContext(request, VoiceClient) -> JSONResponse:
    if "context" not in request.json:
        abort(400, "Bad data `context`")

    VoiceClient.Context.update(request.json["context"])

    return JSONResponse({"context": VoiceClient.Context})


@app.get("/getSource")
@authorized
async def getSource(request) -> JSONResponse:
    Query = "".join(request.args.get("query", [])).strip()
    if not Query:
        abort(400, "Missing parameter query.")

    return JSONResponse({"source": await AudioData.create(Query)})


@app.get("/searchSources")
@authorized
async def searchSources(request) -> JSONResponse:
    Query = "".join(request.args.get("query", [])).strip()
    if not Query:
        abort(400, "Missing parameter query.")

    return JSONResponse(
        {"sources": filter(lambda Source: AudioData(Source), await search(Query))}
    )


@app.post("/putSource")
@authorized
@need_voiceclient
async def putSource(request, VoiceClient) -> JSONResponse:
    if "source" not in request.json:
        abort(400, "Bad data `source`")

    index = VoiceClient.putSource(request.json["source"])

    return JSONResponse({"index": index})


@app.post("/loadSource")
@authorized
@need_voiceclient
async def loadSource(request, VoiceClient) -> JSONResponse:
    if "query" not in request.json:
        abort(400, "Bad data `query`")

    Source = await VoiceClient.loadSource(request.json["query"])

    return JSONResponse({"source": Source})


@app.post("/setVolume")
@authorized
@need_voiceclient
async def setVolume(request, VoiceClient) -> response.empty:
    if "volume" not in request.json or not isinstance(request.json["volume"], float):
        abort(400, "Bad data `volume`")

    VoiceClient.volume = request.json["volume"]

    return response.empty()


@app.post("/setCrossfade")
@authorized
@need_voiceclient
async def setCrossfade(request, VoiceClient) -> response.empty:
    if "crossfade" not in request.json or not isinstance(
        request.json["crossfade"], float
    ):
        abort(400, "Bad data `crossfade`")

    VoiceClient.crossfade = request.json["crossfade"]

    return response.empty()


@app.post("/setAutoplay")
@authorized
@need_voiceclient
async def setAutoplay(request, VoiceClient) -> response.empty:
    if "autoplay" not in request.json or not isinstance(request.json["autoplay"], bool):
        abort(400, "Bad data `autoplay`")

    VoiceClient.autoplay = request.json["autoplay"]

    return response.empty()


@app.post("/setFilter")
@authorized
@need_voiceclient
async def setFilter(request, VoiceClient) -> response.empty:
    if "filter" not in request.json or not isinstance(request.json["filter"], dict):
        abort(400, "Bad data `filter`")

    VoiceClient.filter = request.json["filter"]

    return response.empty()


@app.post("/seek")
@authorized
@need_voiceclient
async def seek(request, VoiceClient) -> response.empty:
    if "offset" not in request.json or not isinstance(request.json["offset"], float):
        abort(400, "Bad data `offset`")

    await VoiceClient.seek(request.json["offset"])

    return response.empty()


@app.post("/skip")
@authorized
@need_voiceclient
async def skip(request, VoiceClient) -> JSONResponse:
    if "offset" not in request.json or not isinstance(request.json["offset"], int):
        abort(400, "Bad data `offset`")

    VoiceClient.skip(request.json["offset"])

    return JSONResponse({"remain": len(VoiceClient.Queue)})


@app.post("/pause")
@authorized
@need_voiceclient
async def pause(request, VoiceClient) -> response.empty:
    VoiceClient.pause()

    return response.empty()


@app.post("/resume")
@authorized
@need_voiceclient
async def resume(request, VoiceClient) -> response.empty:
    VoiceClient.resume()

    return response.empty()


@app.post("/shuffle")
@authorized
@need_voiceclient
async def shuffle(request, VoiceClient) -> JSONResponse:
    VoiceClient.shuffle()

    return JSONResponse({"entries": VoiceClient.Queue})


@app.post("/remove")
@authorized
@need_voiceclient
async def remove(request, VoiceClient) -> JSONResponse:
    if "index" not in request.json or not isinstance(request.json["index"], int):
        abort(400, "Bad data `index`")

    removed = VoiceClient.Queue[request.json["index"] - 1]
    del VoiceClient.Queue[request.json["index"] - 1]

    return JSONResponse({"removed": removed, "entries": VoiceClient.Queue})


@app.get("/state")
@authorized
@need_voiceclient
async def state(request, VoiceClient) -> JSONResponse:
    return JSONResponse(
        {
            "id": VoiceClient.id,
            "guild_id": VoiceClient.guild_id,
            "channel_id": VoiceClient.channel_id,
            "state": VoiceClient.state,
            "current": VoiceClient.current,
            "duration": VoiceClient.current.duration,
            "position": VoiceClient.current.position,
            "remain": VoiceClient.current.remain,
            "remainQueue": len(VoiceClient.Queue),
            "options": {
                "autoplay": VoiceClient.autoplay,
                "volume": VoiceClient.volume,
                "crossfade": VoiceClient.crossfade,
                "filter": VoiceClient.filter,
            },
        }
    )


@app.get("/queue")
@authorized
@need_voiceclient
async def queue(request, VoiceClient) -> JSONResponse:
    return JSONResponse(
        {
            "entries": VoiceClient.Queue,
        }
    )
