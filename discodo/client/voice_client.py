import asyncio

from ..errors import NodeException
from ..utils import EventDispatcher
from .http import HTTPClient


class VoiceClient:
    def __init__(self, Node, id: str, guild_id: int) -> None:
        self.Node = Node
        self.loop = Node.loop

        self.id = id
        self.guild_id = guild_id
        self.channel_id: int = None

        self.http = HTTPClient(self)
        self.dispatcher = EventDispatcher()

        self.dispatcher.on("VC_CHANNEL_EDITED", self.__channel_editied)

    def __repr__(self) -> str:
        return f"<VoiceClient id={self.id} guild_id={self.guild_id} channel_id={self.channel_id} Node={self.Node}>"

    def __del__(self):
        vc = self.Node.voiceClients.get(self.guild_id)
        if vc and vc == self:
            self.Node.voiceClients.pop(self.guild_id)

    def __channel_editied(self, channel_id: int) -> None:
        self.channel_id: int = channel_id

    async def send(self, Operation: str, Data: dict = {}):
        Data["guild_id"] = self.guild_id

        return await self.Node.send(Operation, Data)

    async def query(
        self, Operation: str, Data: dict = {}, Event: str = None, timeout: float = 10.0
    ) -> dict:
        if not Event:
            Event = Operation

        Future = self.loop.create_task(
            self.dispatcher.wait_for(
                Event,
                condition=lambda Data: int(Data["guild_id"]) == int(self.guild_id),
                timeout=timeout,
            )
        )

        await self.send(Operation, Data)

        Data = await Future

        if Data.get("traceback"):
            raise NodeException(*list(Data["traceback"].items())[0])

        return Data

    async def getVCContext(self, ws: bool = True) -> dict:
        if ws:
            return (await self.query("getVCContext"))["context"]

        return await self.http.getVCContext()

    async def setVCContext(self, context: dict, ws: bool = True) -> dict:
        if ws:
            return (await self.query("setVCContext", {"context": context}))["context"]

        return await self.http.setVCContext(context)

    async def getSource(self, Query: str, ws: bool = True) -> dict:
        if ws:
            return (await self.query("getSource", {"query": Query}))["source"]

        return await self.http.getSource(Query)

    async def searchSources(self, Query: str, ws: bool = True) -> list:
        if ws:
            return (await self.query("searchSources", {"query": Query}))["sources"]

        return await self.http.searchSources(Query)

    async def loadSource(self, Query: str, ws: bool = True) -> dict:
        if ws:
            return (await self.query("loadSource", {"query": Query}))["source"]

        return await self.http.loadSource(Query)

    async def putSource(self, Source: dict, ws: bool = True) -> int:
        if ws:
            return (await self.query("putSource", {"song": Source}))["index"]

        return await self.http.putSource(Source)

    async def skip(self, offset: int = 1, ws: bool = True) -> int:
        if ws:
            return (await self.query("skip", {"offset": offset}))["remain"]

        return await self.http.skip(offset)

    async def seek(self, offset: float, ws: bool = True) -> dict:
        if ws:
            return await self.query("seek", {"offset": offset})

        return await self.http.seek(offset)

    async def setVolume(self, volume: int, ws: bool = True) -> float:
        if ws:
            return (await self.query("setVolume", {"volume": volume}))["volume"]

        return await self.http.setVolume(volume)

    async def setCrossfade(self, crossfade: float, ws: bool = True) -> float:
        if ws:
            return (await self.query("setCrossfade", {"crossfade": crossfade}))[
                "crossfade"
            ]

        return await self.http.setCrossfade(crossfade)

    async def setAutoplay(self, autoplay: bool, ws: bool = True) -> bool:
        if ws:
            return (await self.query("setAutoplay", {"autoplay": autoplay}))["autoplay"]

        return await self.http.setAutoplay(autoplay)

    async def setFilter(self, filter: dict, ws: bool = True) -> dict:
        if ws:
            return await self.query("setFilter", {"filter": filter})

        return await self.http.setFilter(filter)

    async def pause(self, ws: bool = True) -> dict:
        if ws:
            return await self.query("pause")

        return await self.http.pause()

    async def resume(self, ws: bool = True) -> dict:
        if ws:
            return await self.query("resume")

        return await self.http.resume()

    async def getQueue(self, ws: bool = True) -> list:
        if ws:
            return (await self.query("getQueue"))["entries"]

        return await self.http.getQueue()

    async def getState(self, ws: bool = True) -> dict:
        if ws:
            return await self.query("getState")

        return await self.http.getState()

    async def shuffle(self, ws: bool = True) -> dict:
        if ws:
            return await self.query("shuffle")

        return await self.http.shuffle()

    async def remove(self, index: int, ws: bool = True) -> dict:
        if ws:
            return await self.query("remove", {"index": index})

        return await self.http.remove(index)

    async def requestSubtitle(self, lang: str = None, url: str = None) -> dict:
        if not any([lang, url]):
            raise ValueError("Either `lang` or `url` is needed.")

        Data = {}
        if url:
            Data["url"] = url
        elif lang:
            Data["lang"] = lang

        return await self.query("requestSubtitle", Data)

    async def getSubtitle(self, *args, callback: callable, **kwargs):
        if not asyncio.iscoroutinefunction(callback):
            raise ValueError("Callback function must be coroutine function.")

        Data = await self.requestSubtitle(*args, **kwargs)

        identify_token = Data.get("identify")
        if not identify_token:
            raise ValueError(f"Subtitle not found.")

        _lyricsLock = asyncio.Lock()

        async def lyricsRecieve(lyrics):
            if lyrics["identify"] != identify_token or _lyricsLock.locked():
                return

            await _lyricsLock.acquire()

            try:
                await callback(lyrics)
            finally:
                _lyricsLock.release()

        async def lyricsDone(Data):
            if Data["identify"] != identify_token:
                return

            self.dispatcher.off("Subtitle", lyricsRecieve)
            self.dispatcher.off("subtitleDone", lyricsDone)

        self.dispatcher.on("Subtitle", lyricsRecieve)
        self.dispatcher.on("subtitleDone", lyricsDone)

        return Data

    async def destroy(self) -> dict:
        return await self.query("VC_DESTROY", Event="VC_DESTROYED")
