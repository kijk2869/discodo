import asyncio

from ..utils import EventDispatcher


class VoiceClient:
    def __init__(self, Node, guild_id: int) -> None:
        self.Node = Node
        self.loop = Node.loop
        self.guild_id = guild_id

        self.dispatcher = EventDispatcher()

    def __del__(self):
        vc = self.Node.voiceClients.get(self.guild_id)
        if vc and vc == self:
            self.Node.voiceClients.pop(self.guild_id)

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

        return await Future

    async def loadSource(self, Query: str) -> dict:
        return (await self.query("loadSource", {"query": Query}))["source"]

    async def putSource(self, Source: dict) -> int:
        return (await self.query("putSource", {"song": Source}))["index"]

    async def skip(self, offset: int = 1) -> int:
        return (await self.query("skip", {"offset": offset}))["remain"]

    async def seek(self, offset: float) -> dict:
        return await self.query("seek", {"offset": offset})

    async def setVolume(self, volume: int) -> float:
        return (await self.query("setVolume", {"volume": volume}))["volume"]

    async def setCrossfade(self, crossfade: float) -> float:
        return (await self.query("setCrossfade", {"crossfade": crossfade}))["crossfade"]

    async def setAutoplay(self, autoplay: bool) -> bool:
        return (await self.query("setAutoplay", {"autoplay": autoplay}))["autoplay"]

    async def setGapless(self, gapless: bool) -> bool:
        return (await self.query("setGapless", {"gapless": gapless}))["gapless"]

    async def setFilter(self, filter: dict) -> dict:
        return await self.query("setFilter", {"filter": filter})

    async def pause(self) -> dict:
        return await self.query("pause")

    async def resume(self) -> dict:
        return await self.query("resume")

    async def getQueue(self) -> list:
        return (await self.query("getQueue"))["entries"]

    async def getState(self) -> dict:
        return await self.query("getState")

    async def shuffle(self) -> dict:
        return await self.query("shuffle")

    async def remove(self, index: int) -> dict:
        return await self.query("remove", {"index": index})

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
