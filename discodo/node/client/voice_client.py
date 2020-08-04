import asyncio

from ...utils import EventEmitter


class VoiceClient:
    def __init__(self, Node, guild_id):
        self.Node = Node
        self.guild_id = guild_id

        self.emitter = EventEmitter()

    def __del__(self):
        vc = self.Node.voiceClients.get(self.guild_id)
        if vc and vc is self:
            self.Node.voiceClients.pop(self.guild_id)

    async def send(self, Operation: str, Data: dict = {}):
        Data["guild_id"] = self.guild_id

        return await self.Node.send(Operation, Data)

    async def loadSong(self, Query: str) -> dict:
        await self.send("loadSong", {"query": Query})

        return (await self.emitter.wait_for("loadSong", timeout=10.0))["song"]

    async def putSong(self, Song: dict) -> dict:
        await self.send("putSong", {"song": Song})

        return (await self.emitter.wait_for("putSong", timeout=10.0))["song"]

    async def skip(self, offset: int = 1) -> dict:
        await self.send("skip", {"offset": offset})

        return (await self.emitter.wait_for("skip", timeout=10.0))["remain"]

    async def seek(self, offset: float) -> dict:
        await self.send("seek", {"offset": offset})

        return await self.emitter.wait_for("seek", timeout=10.0)

    async def setVolume(self, volume: int) -> dict:
        await self.send("setVolume", {"volume": volume})

        return (await self.emitter.wait_for("setVolume", timeout=10.0))["volume"]

    async def setCrossfade(self, crossfade: float) -> dict:
        await self.send("setCrossfade", {"crossfade": crossfade})

        return (await self.emitter.wait_for("setCrossfade", timeout=10.0))["crossfade"]

    async def setAutoplay(self, autoplay: bool) -> dict:
        await self.send("setAutoplay", {"autoplay": autoplay})

        return (await self.emitter.wait_for("setAutoplay", timeout=10.0))["autoplay"]

    async def setFilter(self, filter: dict) -> dict:
        await self.send("setFilter", {"filter": filter})

        return await self.emitter.wait_for("setFilter", timeout=10.0)

    async def pause(self) -> dict:
        await self.send("pause")

        return await self.emitter.wait_for("pause", timeout=10.0)

    async def resume(self) -> dict:
        await self.send("resume")

        return await self.emitter.wait_for("resume", timeout=10.0)

    async def repeat(self, repeat: bool) -> dict:
        await self.send("repeat", {"repeat": repeat})

        return (await self.emitter.wait_for("repeat", timeout=10.0))["repeat"]

    async def changePause(self) -> dict:
        await self.send("changePause")

        return await self.emitter.wait_for("changePause", timeout=10.0)

    async def getQueue(self) -> dict:
        await self.send("getQueue")

        return (await self.emitter.wait_for("Queue", timeout=10.0))["entries"]

    async def getState(self) -> dict:
        await self.send("getState")

        return await self.emitter.wait_for("State", timeout=10.0)

    async def shuffle(self) -> dict:
        await self.send("shuffle")

        return await self.emitter.wait_for("shuffle", timeout=10.0)

    async def remove(self, index: int) -> dict:
        await self.send("remove", {"index": index})

        return await self.emitter.wait_for("remove", timeout=10.0)

    async def requestLyrics(self, language: str) -> dict:
        await self.send("requestLyrics", {"language": language})

        return await self.emitter.wait_for("requestLyrics", timeout=10.0)

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
