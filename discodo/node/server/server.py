import asyncio
import json
import os
from threading import local
import uuid

import aiohttp
from sanic import Sanic, response
from sanic.exceptions import abort

from ...AudioSource import AudioData
from ...planner import IPRotator
from ...stat import getStat
from .websocket import app as WebsocketBlueprint

app = Sanic(__name__)
app.stream_authorize = uuid.uuid4()


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


class StreamSender:
    def __init__(self, session, response):
        self.loop = asyncio.get_event_loop()
        self.session = session
        self.response = response

    def __del__(self):
        if self.response:
            self.response.close()
        self.loop.create_task(self.session.close())

    @classmethod
    async def create(cls, url, headers={}, session_kwargs={}):
        if "host" in headers:
            del headers["host"]

        session = aiohttp.ClientSession(**session_kwargs)
        response = await session.get(url, headers=headers)

        return cls(session, response)

    async def send(self, response):
        try:
            async for data, _ in self.response.content.iter_chunks():
                if len(data) < 1:
                    break

                try:
                    await response.write(data)
                except:
                    break
        except:
            pass
        finally:
            self.__del__()


@app.route("/stream")
async def streamSong(request):
    url = "".join(request.args.get("url", [])).strip()
    if not url:
        abort(400, "Missing parameter url.")

    local_addr = "".join(request.args.get("localaddr", [])).strip()
    Connector = aiohttp.TCPConnector(local_addr=(local_addr, 0)) if local_addr else None

    try:
        StreamServer = await StreamSender.create(
            url, headers=request.headers, session_kwargs={"connector": Connector}
        )
    except aiohttp.client_exceptions.ClientConnectorError:
        abort(400, "Unavailable local address.")

    return response.stream(
        StreamServer.send,
        status=StreamServer.response.status,
        headers=StreamServer.response.headers,
    )


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
