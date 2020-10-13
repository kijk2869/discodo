import asyncio

import aiohttp
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse

from .. import __version__
from ..config import Config
from ..source import AudioData
from ..status import getStatus
from .planner import app as PlannerBlueprint
from .websocket import app as WebsocketBlueprint

app = FastAPI()
app.include_router(WebsocketBlueprint)
app.include_router(PlannerBlueprint)


def authorized(Authorization: str = Header(None)) -> str:
    if Authorization != Config.PASSWORD:
        raise HTTPException(403, "Password mismatch.")

    return Authorization


@app.route("/")
async def index(request: Request):
    return HTMLResponse(f"<h1>Discodo</h1> <h3>{__version__}")


@app.get("/status")
async def status() -> dict:
    return getStatus()


@app.get("/getSource", dependencies=[Depends(authorized)])
async def getSource(Query: str = None) -> dict:
    if not Query:
        raise HTTPException(400, "Missing parameter query.")

    return await AudioData.create(Query)
