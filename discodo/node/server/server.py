import asyncio
import json
import os

import aiohttp
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import StreamingResponse

from ...AudioSource import AudioData
from ...planner import IPRotator
from ...stat import getStat
from .websocket import app as WebsocketBlueprint

app = FastAPI()


@app.on_event("startup")
async def applyVariables():
    os.environ["USE_SERVER"] = "1"
    app.PASSWORD = os.getenv("PASSWORD", "hellodiscodo")

    USABLE_IP = json.loads(os.getenv("USABLE_IP", "[]"))

    app.planner = IPRotator() if USABLE_IP else None
    for IP in USABLE_IP if USABLE_IP else []:
        app.planner.add(IP)


app.include_router(WebsocketBlueprint)


def authorized(Authorization: str = Header(None)):
    if Authorization != app.PASSWORD:
        raise HTTPException(403, "Password mismatch.")

    return Authorization


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

    async def send(self):
        try:
            async for data, _ in self.response.content.iter_chunks():
                yield data
        except:
            pass
        finally:
            self.__del__()


@app.route("/stream")
async def streamSong(request: Request):
    if request.query_params["auth"] != app.PASSWORD:
        raise HTTPException(403, "Password mismatch.")
    url = request.query_params["url"]
    if not url:
        raise HTTPException(400, "Missing parameter url.")

    local_addr = request.query_params["localaddr"]

    Connector = aiohttp.TCPConnector(local_addr=(local_addr, 0)) if local_addr else None

    try:
        StreamServer = await StreamSender.create(
            url, headers=dict(request.headers), session_kwargs={"connector": Connector}
        )
    except aiohttp.client_exceptions.ClientConnectorError:
        raise HTTPException(400, "Unavailable local address.")

    return StreamingResponse(
        StreamServer.send(),
        status_code=StreamServer.response.status,
        headers=StreamServer.response.headers,
    )


@app.get("/stat")
async def stat():
    return getStat()


@app.get("/getSong", dependencies=[Depends(authorized)])
async def getSong(query: str = None):
    if not query:
        raise HTTPException(400, "Missing parameter query.")

    return await AudioData.create(query, app.planner)
