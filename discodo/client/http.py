from http.client import responses
from typing import Union

import aiohttp

from ..errors import DiscodoException


class HTTPException(DiscodoException):
    def __init__(self, status: int) -> None:
        super().__init__(f"{status} {responses.get(status, 'Unknown Status Code')}")


class HTTPClient:
    def __init__(self, client) -> None:
        self.VoiceClient = client
        self.Node = client.Node
        self.loop = client.Node.loop

    @property
    def headers(self) -> dict:
        return {
            "Authorization": self.Node.password,
            "User-ID": str(self.Node.user_id),
            "Guild-ID": str(self.VoiceClient.guild_id),
            "VoiceClient-ID": str(self.VoiceClient.id),
        }

    async def fetch(self, method: str, endpoint: str, **kwargs) -> dict:
        URL = self.Node.URL + endpoint

        async with aiohttp.ClientSession(headers=self.headers) as session:
            async with session.request(method, URL, **kwargs) as response:
                if 200 <= response.status < 300:
                    return await response.json(content_type=None)

                raise HTTPException(response.status)

    async def getVCContext(self) -> dict:
        return (await self.fetch("GET", "/getVCContext"))["source"]

    async def setVCContext(self, context: dict) -> dict:
        return (await self.fetch("POST", "/setVCContext", json={"context": context}))[
            "context"
        ]

    async def getSource(self, query: str) -> dict:
        return (await self.fetch("GET", "/getSource", params={"query": query}))[
            "source"
        ]

    async def searchSource(self, query: str) -> list:
        return (await self.fetch("GET", "/searchSource", params={"query": query}))[
            "sources"
        ]

    async def putSource(self, source: dict) -> Union[int, list]:
        return (await self.fetch("POST", "/putSource", json={"source": dict(source)}))[
            "index"
        ]

    async def loadSource(self, query: str) -> dict:
        return (await self.fetch("POST", "/loadSource", json={"query": str(query)}))[
            "source"
        ]

    async def setVolume(self, volume: float) -> None:
        return await self.fetch("POST", "/setVolume", json={"volume": float(volume)})

    async def setCrossfade(self, crossfade: float) -> None:
        return await self.fetch(
            "POST", "/setCrossfade", json={"crossfade": float(crossfade)}
        )

    async def setAutoplay(self, autoplay: bool) -> None:
        return await self.fetch(
            "POST", "/setAutoplay", json={"autoplay": bool(autoplay)}
        )

    async def setFilter(self, filter: dict) -> None:
        return await self.fetch("POST", "/setFilter", json={"filter": dict(filter)})

    async def seek(self, offset: float) -> None:
        return await self.fetch("POST", "/seek", json={"offset": float(offset)})

    async def skip(self, offset: int) -> None:
        return (await self.fetch("POST", "/skip", json={"offset": int(offset)}))[
            "remain"
        ]

    async def pause(self) -> None:
        return await self.fetch("POST", "/pause")

    async def resume(self) -> None:
        return await self.fetch("POST", "/pause")

    async def shuffle(self) -> None:
        return await self.fetch("POST", "/shuffle")

    async def remove(self, index: int) -> None:
        return await self.fetch("POST", "/remove", json={"index": int(index)})

    async def getState(self) -> dict:
        return await self.fetch("GET", "/state")

    async def getQueue(self) -> dict:
        return (await self.fetch("GET", "/queue"))["entries"]
