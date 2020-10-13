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


def need_voiceclient(func: Coroutine) -> Coroutine:
    def wrapper(request, *args, **kwargs):
        user_id = int(request.headers.get("User-ID"))

        if (
            not hasattr(request.app, "ClientManager")
            or not user_id in request.app.ClientManager
        ):
            abort(404, "ClientManager not found.")

        manager = request.app.ClientManager[user_id]

        guild_id = int(request.headers.get("Guild-ID"))

        VoiceClient = manager.getVC(guild_id, safe=True)

        VoiceClientID = request.headers.get("VoiceClient-ID")

        if not VoiceClient:
            abort(404, "VoiceClient not found.")

        if VoiceClientID != VoiceClient.id:
            abort(403, "VoiceClient ID mismtach.")

        return func(request, VoiceClient, *args, **kwargs)

    return wrapper


@app.get("/getSource")
@authorized
async def getSource(request) -> response.json:
    Query = "".join(request.args.get("query", [])).strip()
    if not Query:
        abort(400, "Missing parameter query.")

    return response.json({"source": await AudioData.create(Query)})


@app.post("/putSource")
@authorized
@need_voiceclient
async def putSource(request, VoiceClient) -> response.json:
    if "source" not in request.json:
        abort(400, "Bad data `source`")

    index = VoiceClient.putSource(request.json["source"])

    return response.json({"index": index})


@app.post("/loadSource")
@authorized
@need_voiceclient
async def loadSource(request, VoiceClient) -> response.json:
    if "query" not in request.json:
        abort(400, "Bad data `query`")

    Source = await VoiceClient.loadSource(request.json["query"])

    return response.json({"source": Source})


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


@app.post("/setGapless")
@authorized
@need_voiceclient
async def setGapless(request, VoiceClient) -> response.empty:
    if "gapless" not in request.json or not isinstance(request.json["gapless"], bool):
        abort(400, "Bad data `gapless`")

    VoiceClient.gapless = request.json["gapless"]

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
async def seek(request, VoiceClient) -> response.json:
    if "offset" not in request.json or not isinstance(request.json["offset"], int):
        abort(400, "Bad data `offset`")

    VoiceClient.skip(request.json["offset"])

    return response.json({"remain": len(VoiceClient.Queue)})


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
async def shuffle(request, VoiceClient) -> response.json:
    VoiceClient.shuffle()

    return response.json({"entries": VoiceClient.Queue})


@app.post("/remove")
@authorized
@need_voiceclient
async def remove(request, VoiceClient) -> response.json:
    if "index" not in request.json or not isinstance(request.json["index"], int):
        abort(400, "Bad data `index`")

    removed = VoiceClient.Queue[request.json["index"] - 1]
    del VoiceClient.Queue[request.json["index"] - 1]

    return response.json({"removed": removed, "entries": VoiceClient.Queue})


@app.get("/state")
@authorized
@need_voiceclient
async def resume(request, VoiceClient) -> response.json:
    return response.json(
        {
            "id": VoiceClient.id,
            "guild_id": VoiceClient.guild_id,
            "channel_id": VoiceClient.channel_id,
            "state": VoiceClient.state,
            "current": VoiceClient.current,
            "duration": VoiceClient.current.duration,
            "position": VoiceClient.current.position,
            "remain": VoiceClient.current.remain,
            "options": {
                "autoplay": VoiceClient.autoplay,
                "volume": VoiceClient.volume,
                "crossfade": VoiceClient.crossfade,
                "gapless": VoiceClient.gapless,
                "filter": VoiceClient.filter,
            },
        }
    )


@app.get("/queue")
@authorized
@need_voiceclient
async def queue(request, VoiceClient) -> response.json:
    return response.json({"entries": VoiceClient.Queue})
