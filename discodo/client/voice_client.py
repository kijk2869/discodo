import asyncio
import contextlib
import logging

from ..errors import NodeException
from ..utils import EventDispatcher
from .http import HTTPClient
from .models import AudioData, AudioSource, Queue, ensureQueueObjectType


class VoiceClient:
    def __init__(self, Node, id, guild_id):
        self.Node = Node
        self.client = Node.client
        self.loop = Node.loop

        self.id = id
        self.guild_id = guild_id
        self.channel_id = None

        self.http = HTTPClient(self)
        self.dispatcher = EventDispatcher()

        self.dispatcher.on(
            "VC_CHANNEL_EDITED",
            lambda data: setattr(self, "channel_id", data["channel_id"]),
        )

        self._volume = 1.0
        self._crossfade = 10.0
        self._autoplay = True
        self._filter = {}

        self.dispatcher.on("getState", self.handleGetState)

        self.loop.create_task(self.send("getState", {}))

        self.Queue = Queue(self)

        self.dispatcher.on("getQueue", self.Queue.handleGetQueue)
        self.dispatcher.on("QUEUE_EVENT", self.Queue.handleQueueEvent)

        self.loop.create_task(self.send("getQueue", {}))

    def __repr__(self) -> str:
        return f"<VoiceClient id={self.id} guild_id={self.guild_id} channel_id={self.channel_id} Node={self.Node}>"

    def __del__(self):
        vc = self.Node.voiceClients.get(self.guild_id)
        if vc and vc == self:
            self.Node.voiceClients.pop(self.guild_id)

    @property
    def volume(self):
        return self._volume

    @property
    def crossfade(self):
        return self._crossfade

    @property
    def autoplay(self):
        return self._autoplay

    @property
    def filter(self):
        return self._filter

    def handleGetState(self, data):
        options = data["options"]

        self._volume = options["volume"]
        self._crossfade = options["crossfade"]
        self._autoplay = options["autoplay"]
        self._filter = options["filter"]

        self.channel_id = data["channel_id"]

    async def send(self, op, data):
        data["guild_id"] = self.guild_id

        return await self.Node.send(op, data)

    async def query(self, op, data=None, event=None, timeout=10.0):
        if not event:
            event = op
        if not data:
            data = {}

        Task = self.loop.create_task(
            self.dispatcher.wait_for(
                event,
                condition=lambda d: int(d["guild_id"]) == int(self.guild_id),
                timeout=timeout,
            )
        )

        await self.send(op, data)

        Data = await Task

        if Data.get("traceback"):
            raise NodeException(*list(Data["traceback"].items())[0])

        return Data

    async def getContext(self):
        return await self.http.getVCContext()

    async def setContext(self, data):
        return await self.http.setVCContext(data)

    async def getSource(self, query):
        data = await self.http.getSource(query)

        return ensureQueueObjectType(self, data["source"])

    async def searchSources(self, query):
        data = await self.http.searchSources(query)

        return ensureQueueObjectType(self, data["sources"])

    async def putSource(self, source):
        data = await self.http.putSource(
            list(map(lambda x: x.data, source))
            if isinstance(source, list)
            else source.data
        )

        return ensureQueueObjectType(self, data["source"])

    async def loadSource(self, query):
        data = await self.http.loadSource(query)

        return ensureQueueObjectType(self, data["source"])

    async def skip(self, offset=1):
        return await self.http.skip(offset)

    async def seek(self, offset):
        return await self.http.seek(offset)

    async def getOptions(self):
        return await self.http.getOptions()

    async def setOptions(self, **options):
        if "volume" in options:
            self._volume = options["volume"]
        if "crossfade" in options:
            self._crossfade = options["crossfade"]
        if "autoplay" in options:
            self._autoplay = options["autoplay"]
        if "filter" in options:
            self._filter = options["filter"]

        return await self.http.setOptions(options)

    async def setVolume(self, volume):
        return await self.setOptions(volume=volume)

    async def setCrossfade(self, crossfade):
        return await self.setOptions(crossfade=crossfade)

    async def setAutoplay(self, autoplay):
        return await self.setOptions(autoplay=autoplay)

    async def setFilter(self, filter):
        return await self.setOptions(filter=filter)

    async def pause(self):
        return await self.http.pause()

    async def resume(self):
        return await self.http.resume()

    async def shuffle(self):
        data = await self.http.shuffle()

        self.Queue.handleGetQueue(data)

        return self.Queue

    async def getState(self):
        data = await self.query("getState")

        data["current"] = ensureQueueObjectType(self, data["current"])

        return data

    async def fetchQueue(self, ws=True):
        if ws:
            await self.query("getQueue")
        else:
            self.Queue.handleGetQueue(await self.http.queue())

        return self.Queue

    async def requestSubtitle(self, lang=None, url=None):
        if not any([lang, url]):
            raise ValueError("Either `lang` or `url` is needed.")

        Data = {}
        if url:
            Data["url"] = url
        elif lang:
            Data["lang"] = lang

        return await self.query("requestSubtitle", Data)

    async def getSubtitle(self, *args, callback, **kwargs):
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

    async def moveTo(self, node):
        if node == self.Node:
            raise ValueError("Already connected to this node.")

        channel = self.client.client.get_channel(self.channel_id)

        if not channel:
            raise ValueError("this voice client is not connected to the channel.")

        State = await self.getState()

        await self.destroy()

        VC = await self.client.connect(channel, node)

        await VC.setOptions(
            volume=self.volume,
            crossfade=self.crossfade,
            autoplay=self.autoplay,
            filter=self.filter,
        )

        await VC.putSource(
            ([State["current"]] if State["current"] else []) + self.Queue
        )

        return VC

    async def destroy(self):
        return await self.query("VC_DESTROY", event="VC_DESTROYED")
