import functools
import json

from sanic import Blueprint, response
from sanic.exceptions import abort

from ..config import Config
from ..source import AudioData

app = Blueprint(__name__)


def authorized(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        if request.headers.get("Authorization") != Config.PASSWORD:
            abort(403, "Password mismatch.")

        return func(request, *args, **kwargs)

    return wrapper


def need_manager(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        tag = str(request.headers.get("User-ID")) + (
            f"-{request.headers.get('Shard-ID')}"
            if request.headers.get("Shard-ID") is not None
            else ""
        )

        if (
            not hasattr(request.app.ctx, "ClientManagers")
            or not tag in request.app.ctx.ClientManagers
        ):
            abort(404, "ClientManager not found.")

        manager = request.app.ctx.ClientManagers[tag]

        return func(request, manager, *args, **kwargs)

    return wrapper


def need_voiceclient(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        tag = str(request.headers.get("User-ID")) + (
            f"-{request.headers.get('Shard-ID')}"
            if request.headers.get("Shard-ID") is not None
            else ""
        )

        if (
            not hasattr(request.app.ctx, "ClientManagers")
            or not tag in request.app.ctx.ClientManagers
        ):
            abort(404, "ClientManager not found.")

        manager = request.app.ctx.ClientManagers[tag]

        guild_id = str(request.headers.get("Guild-ID"))

        VoiceClient = manager.getVC(guild_id, safe=True)

        VoiceClientID = request.headers.get("VoiceClient-ID")

        if not VoiceClient:
            abort(404, "VoiceClient not found.")

        if VoiceClientID != VoiceClient.id:
            abort(403, "VoiceClient ID mismtach.")

        return func(request, VoiceClient, *args, **kwargs)

    return wrapper


class Encoder(json.JSONEncoder):
    @staticmethod
    def default(o):
        return o.toDict()


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


@app.get("/getSource")
@authorized
async def getSource(request):
    Query = "".join(request.args.get("query", [])).strip()
    if not Query:
        abort(400, "Missing parameter query.")

    return JSONResponse({"source": await AudioData.create(Query)})


@app.get("/searchSources")
@authorized
async def searchSources(request):
    Query = "".join(request.args.get("query", [])).strip()
    if not Query:
        abort(400, "Missing parameter query.")

    return JSONResponse({"sources": await AudioData.create(Query, search=True)})


@app.get("/context")
@authorized
@need_voiceclient
async def getContext(request, VoiceClient):
    return JSONResponse(VoiceClient.Context)


@app.post("/context")
@authorized
@need_voiceclient
async def setContext(request, VoiceClient):
    VoiceClient.Context = request.json["context"]

    return JSONResponse(VoiceClient.Context)


@app.post("/putSource")
@authorized
@need_voiceclient
async def putSource(request, VoiceClient):
    if "source" not in request.json:
        abort(400, "Bad data `source`")

    source = (
        list(map(AudioData, request.json["source"]))
        if isinstance(request.json["source"], list)
        else AudioData(request.json["source"])
    )
    VoiceClient.putSource(source)

    return JSONResponse({"source": source})


@app.post("/loadSource")
@authorized
@need_voiceclient
async def loadSource(request, VoiceClient):
    if "query" not in request.json:
        abort(400, "Bad data `query`")

    Source = await VoiceClient.loadSource(request.json["query"])

    return JSONResponse({"source": Source})


@app.get("/options")
@authorized
@need_voiceclient
async def getOptions(request, VoiceClient):
    return JSONResponse(
        {
            "autoplay": VoiceClient.autoplay,
            "volume": VoiceClient.volume,
            "crossfade": VoiceClient.crossfade,
            "filter": VoiceClient.filter,
        }
    )


@app.post("/options")
@authorized
@need_voiceclient
async def setOptions(request, VoiceClient):
    if "volume" in request.json:
        VoiceClient.volume = request.json["volume"]

    if "crossfade" in request.json:
        VoiceClient.crossfade = request.json["crossfade"]

    if "autoplay" in request.json:
        VoiceClient.autoplay = request.json["autoplay"]

    if "filter" in request.json:
        VoiceClient.filter = request.json["filter"]

    return JSONResponse(
        {
            "autoplay": VoiceClient.autoplay,
            "volume": VoiceClient.volume,
            "crossfade": VoiceClient.crossfade,
            "filter": VoiceClient.filter,
        }
    )


@app.get("/seek")
@authorized
@need_voiceclient
async def getSeek(request, VoiceClient):
    return JSONResponse(
        {
            "duration": VoiceClient.current.duration,
            "position": VoiceClient.current.position,
            "remain": VoiceClient.current.remain,
        }
    )


@app.post("/seek")
@authorized
@need_voiceclient
async def seek(request, VoiceClient):
    if "offset" not in request.json:
        abort(400, "Bad data `offset`")

    await VoiceClient.seek(request.json["offset"])

    return response.empty()


@app.post("/skip")
@authorized
@need_voiceclient
async def skip(request, VoiceClient):
    offset = request.json.get("offset", 1)

    VoiceClient.skip(offset)

    return response.empty()


@app.post("/pause")
@authorized
@need_voiceclient
async def pause(request, VoiceClient):
    VoiceClient.pause()

    return response.empty()


@app.post("/resume")
@authorized
@need_voiceclient
async def resume(request, VoiceClient):
    VoiceClient.resume()

    return response.empty()


@app.post("/shuffle")
@authorized
@need_voiceclient
async def shuffle(request, VoiceClient):
    VoiceClient.shuffle()

    return JSONResponse({"entries": VoiceClient.Queue})


@app.get("/current")
@authorized
@need_voiceclient
async def current(request, VoiceClient):
    return JSONResponse(VoiceClient.current)


@app.get("/queue")
@authorized
@need_voiceclient
async def queue(request, VoiceClient):
    return JSONResponse(
        {
            "entries": VoiceClient.Queue,
        }
    )


@app.get("/queue/<index:int>")
@authorized
@need_voiceclient
async def queueItem(request, VoiceClient, index):
    return JSONResponse(VoiceClient.Queue[index])


@app.get("/queue/<tag:string>")
@authorized
@need_voiceclient
async def queueItemTag(request, VoiceClient, tag):
    searched = list(filter(lambda x: x.tag == tag, VoiceClient.Queue))

    return JSONResponse(searched.pop(0))


@app.post("/current")
@authorized
@need_voiceclient
async def changeCurrent(request, VoiceClient):
    source = VoiceClient.current

    if "context" in request.json:
        source.Context = request.json["context"]

    return JSONResponse(source)


@app.post("/queue/<index:int>")
@authorized
@need_voiceclient
async def changeQueueItem(request, VoiceClient, index):
    source = VoiceClient.Queue[index]

    if "index" in request.json:
        source = VoiceClient.Queue.pop(index)
        VoiceClient.Queue.insert(index, source)

    if "context" in request.json:
        source.Context = request.json["context"]

    if "start_position" in request.json:
        source.start_position = request.json["start_position"]

    return JSONResponse(source)


@app.post("/queue/<tag:string>")
@authorized
@need_voiceclient
async def changeQueueItemTag(request, VoiceClient, tag):
    searched = list(filter(lambda x: x.tag == tag, VoiceClient.Queue))
    source, index = searched[0], VoiceClient.Queue.index(searched[0])

    if "index" in request.json:
        source = VoiceClient.Queue.pop(index)
        VoiceClient.Queue.insert(index, source)

    if "context" in request.json:
        source.Context = request.json["context"]

    if "start_position" in request.json:
        source.start_position = request.json["start_position"]

    return JSONResponse(source)


@app.delete("/queue/<index:int>")
@authorized
@need_voiceclient
async def removeQueueItem(request, VoiceClient, index):
    removed = VoiceClient.Queue[index]
    del VoiceClient.Queue[index]

    return JSONResponse({"removed": removed, "entries": VoiceClient.Queue})


@app.delete("/queue/<tag:string>")
@authorized
@need_voiceclient
async def removeQueueItemTag(request, VoiceClient, tag):
    searched = list(filter(lambda x: x.tag == tag, VoiceClient.Queue))
    index = VoiceClient.Queue.index(searched[0])

    removed = VoiceClient.Queue[index]
    del VoiceClient.Queue[index]

    return JSONResponse({"removed": removed, "entries": VoiceClient.Queue})
