import asyncio

from ...utils import EventEmitter


class VoiceClient:
    def __init__(self, Node, guild_id):
        self.Node = Node
        self.loop = asyncio.get_event_loop()
        self.guild_id = guild_id

        self.emitter = EventEmitter()

    def __del__(self):
        vc = self.Node.voiceClients.get(self.guild_id)
        if vc and vc is self:
            self.Node.voiceClients.pop(self.guild_id)

    async def send(self, Operation: str, Data: dict = {}):
        Data["guild_id"] = self.guild_id

        return await self.Node.send(Operation, Data)

    async def query(
        self, Operation: str, Data: dict = {}, Event: str = None, timeout: float = 10.0
    ) -> dict:
        if not Event:
            Event = Operation

        Future = self.loop.create_task(self.emitter.wait_for(Event, timeout=timeout))

        await self.send(Operation, Data)

        return await Future

    async def loadSong(self, Query: str) -> dict:
        return (await self.query("loadSong", {"query": Query}))["song"]

    async def putSong(self, Song: dict) -> dict:
        return (await self.query("putSong", {"song": Song}))["song"]

    async def skip(self, offset: int = 1) -> dict:
        return (await self.query("skip", {"offset": offset}))["remain"]

    async def seek(self, offset: float) -> dict:
        return await self.query("seek", {"offset": offset})

    async def setVolume(self, volume: int) -> dict:
        return (await self.query("setVolume", {"volume": volume}))["volume"]

    async def setCrossfade(self, crossfade: float) -> dict:
        return (await self.query("setCrossfade", {"crossfade": crossfade}))["crossfade"]

    async def setAutoplay(self, autoplay: bool) -> dict:
        return (await self.query("setAutoplay", {"autoplay": autoplay}))["autoplay"]

    async def setFilter(self, filter: dict) -> dict:
        return await self.query("setFilter", {"filter": filter})

    async def pause(self) -> dict:
        return await self.query("pause")

    async def resume(self) -> dict:
        return await self.query("resume")

    async def repeat(self, repeat: bool) -> dict:
        return (await self.query("repeat", {"repeat": repeat}))["repeat"]

    async def changePause(self) -> dict:
        return await self.query("changePause")

    async def getQueue(self) -> dict:
        return (await self.query("getQueue", Event="Queue"))["entries"]

    async def getState(self) -> dict:
        return await self.query("getState", Event="State")

    async def shuffle(self) -> dict:
        return await self.query("shuffle")

    async def remove(self, index: int) -> dict:
        return await self.query("remove", {"index": index})

    async def requestLyrics(self, language: str) -> dict:
        return await self.query("requestLyrics", {"language": language})

    async def getLyrics(self, language: str, callback: callable):
        if not asyncio.iscoroutinefunction(callback):
            raise ValueError("Callback function must be coroutine function.")

        Data = await self.requestLyrics(language)

        identify_token = Data.get("identify")
        if not identify_token:
            raise ValueError(f"Lyrics of {language} not found.")

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

            self.emitter.off("Lyrics", lyricsRecieve)
            self.emitter.off("lyricsDone", lyricsDone)

        self.emitter.on("Lyrics", lyricsRecieve)
        self.emitter.on("lyricsDone", lyricsDone)

        return Data

    async def destroy(self) -> dict:
        await self.send("VC_DESTROY")

        return await self.emitter.wait_for("VC_DESTROYED", timeout=10.0)
