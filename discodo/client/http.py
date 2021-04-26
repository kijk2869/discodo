import logging

from ..errors import HTTPException
from .models import ensureQueueObjectType

log = logging.getLogger("discodo.client.http")


class HTTPClient:
    def __init__(self, client):
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

    async def fetch(self, method, endpoint, **kwargs):
        URL = self.Node.URL + endpoint

        if "headers" not in kwargs:
            kwargs["headers"] = {}

        kwargs["headers"].update(self.headers)

        async with self.Node.session.request(method, URL, **kwargs) as response:
            log.debug(f"{method} {URL} with {kwargs} has returned {response.status}")

            data = ensureQueueObjectType(
                self.VoiceClient, await response.json(content_type=None)
            )

            if 200 <= response.status < 300:
                return data

            raise HTTPException(response.status, data)

    async def getSource(self, query):
        return await self.fetch("GET", "/getSource", params={"query": query})

    async def searchSources(self, query):
        return await self.fetch("GET", "/searchSources", params={"query": query})

    async def getVCContext(self):
        return await self.fetch("GET", "/context")

    async def setVCContext(self, data):
        return await self.fetch("POST", "/context", json={"context": data})

    async def putSource(self, source):
        return await self.fetch("POST", "/putSource", json={"source": source})

    async def loadSource(self, query):
        return await self.fetch("POST", "/loadSource", json={"query": query})

    async def getOptions(self):
        return await self.fetch("GET", "/options")

    async def setOptions(self, options):
        return await self.fetch("POST", "/options", json=options)

    async def getSeek(self):
        return await self.fetch("GET", "/seek")

    async def seek(self, offset):
        return await self.fetch("POST", "/seek", json={"offset": offset})

    async def skip(self, offset):
        return await self.fetch("POST", "/skip", json={"offset": offset})

    async def pause(self):
        return await self.fetch("POST", "/pause")

    async def resume(self):
        return await self.fetch("POST", "/resume")

    async def shuffle(self):
        return await self.fetch("POST", "/shuffle")

    async def queue(self):
        return await self.fetch("GET", "/queue")

    async def getCurrent(self):
        return await self.fetch("GET", "/current")

    async def getQueueSource(self, tag):
        return await self.fetch("GET", f"/queue/{tag}")

    async def setCurrent(self, data):
        return await self.fetch("POST", "/current", json=data)

    async def setQueueSource(self, tag, data):
        return await self.fetch("POST", f"/queue/{tag}", json=data)

    async def removeQueueSource(self, tag):
        return await self.fetch("DELETE", f"/queue/{tag}")
