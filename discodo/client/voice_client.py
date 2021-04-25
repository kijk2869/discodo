import asyncio
import copy

from ..enums import PlayerState
from ..errors import NodeException
from ..utils import EventDispatcher
from .http import HTTPClient
from .models import Queue


class VoiceClient:
    """Represents a voice connection of the guild.

    :var discodo.Node Node: The node which the connection is connected with.
    :var discodo.DPYClient client: The client which the connection is binded.
    :var asyncio.AbstractEventLoop loop: The event loop that the client uses for operation.
    :var str id: The id of the voice client, which is used on restful api.
    :var int guild_id: The guild id which is connected to.
    :var Optional[int] channel_id: The channel id which is connected to.
    :var EventDispatcher dispatcher: The event dispatcher that the client dispatches events.
    :var list Queue: The queue of the guild, it is synced to node and readonly."""

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

        self._state = None
        self._volume = 1.0
        self._crossfade = 10.0
        self._autoplay = True
        self._filter = {}
        self._context = {}

        self._current = None

        self.dispatcher.on("getState", self.handleGetState)

        self.syncTask = self.loop.create_task(self.syncWithNode())

        self.Queue = Queue(self)

        self.dispatcher.on("getQueue", self.Queue.handleGetQueue)
        self.dispatcher.on("QUEUE_EVENT", self.Queue.handleQueueEvent)

        self.loop.create_task(self.send("getQueue", {}))

    def __repr__(self) -> str:
        return f"<VoiceClient id={self.id} guild_id={self.guild_id} channel_id={self.channel_id} Node={self.Node}>"

    def __del__(self):
        if self.syncTask and not self.syncTask.done():
            self.syncTask.cancel()

        vc = self.Node.voiceClients.get(self.guild_id)
        if vc and vc == self:
            self.Node.voiceClients.pop(self.guild_id)

    async def syncWithNode(self):
        while True:
            await self.send("getState", {})

            await asyncio.sleep(5.0)

    @property
    def volume(self):
        """Represents the volume of this guild.

        The maximum value is ``2.0``

        .. note::
            This value is a percentage with decimal points. For example, ``100%`` is ``1.0``, and ``5%`` is ``0.05``.

        :rtype: float"""

        return self._volume

    @property
    def crossfade(self):
        """Represents the crossfade duration of this guild.

        :rtype: float"""

        return self._crossfade

    @property
    def autoplay(self):
        """Represents the autoplay state of this guild.

        :rtype: bool"""

        return self._autoplay

    @property
    def filter(self):
        """Represents the autoplay state of this guild.

        .. note::
            For more information, check the documentation of the `FFmpeg Filter`_

        .. _`FFmpeg Filter`: https://ffmpeg.org/ffmpeg-filters.html

        :rtype: bool"""

        return copy.copy(self._filter)

    @property
    def current(self):
        return self._current

    @property
    def duration(self):
        return self._current.duration if self._current else None

    @property
    def position(self):
        return self._current.position if self._current else None

    @property
    def remain(self):
        return round(
            self._current.duration - self._current.position if self._current else None,
            2,
        )

    @property
    def context(self):
        return self._context

    @property
    def state(self):
        return self._state

    def handleGetState(self, data):
        options = data["options"]

        self._volume = options["volume"]
        self._crossfade = options["crossfade"]
        self._autoplay = options["autoplay"]
        self._filter = options["filter"]

        self._current = data["current"]
        self._context = data["context"]
        self._state = PlayerState(data["state"])

        self.channel_id = data["channel_id"]

    async def send(self, op, data):
        """Send websocket payload to the node with guild id

        :param str op: Operation name of the payload
        :param Optional[dict] data: Operation data to send with"""

        data["guild_id"] = str(self.guild_id)

        return await self.Node.send(op, data)

    async def query(self, op, data=None, event=None, timeout=10.0):
        """Send websocket payload to the node with guild id and await response.

        :param str op: Operation name of the payload
        :param Optional[dict] data: Operation data to send with
        :param Optional[str] event: Event name to receive response, defaults to ``op``
        :param Optional[float] timeout: Seconds to wait for response

        :raise asyncio.TimeoutError: The query is timed out.
        :raise discodo.NodeException: The node returned some exceptions.

        :rtype: Any"""

        if not event:
            event = op
        if not data:
            data = {}

        Task = self.loop.create_task(
            self.dispatcher.wait_for(
                event,
                condition=lambda d: d["guild_id"] == str(self.guild_id),
                timeout=timeout,
            )
        )

        await self.send(op, data)

        Data = await Task

        if Data.get("traceback"):
            raise NodeException(*list(Data["traceback"].items())[0])

        return Data

    async def fetchContext(self):
        r"""Fetch the context from the node.

        :rtype: dict"""

        self._context = await self.http.getVCContext()

        return self.context

    async def setContext(self, data):
        r"""Set the context to the node.

        :param dict data: The context to set.

        :rtype: dict"""

        self._context = await self.http.setVCContext(data)

        return self.context

    async def getSource(self, query):
        r"""Search the query and get source from extractor

        :param str query: The query to search.

        :rtype: AudioData"""

        data = await self.http.getSource(query)

        return data["source"]

    async def searchSources(self, query):
        r"""Search the query and get sources from extractor

        :param str query: The query to search.

        :rtype: list[AudioData]"""

        data = await self.http.searchSources(query)

        return data["sources"]

    async def putSource(self, source):
        r"""Search the query and get sources from extractor

        :param source: The source to put on the queue.
        :type source: AudioData or AudioSource or list

        :rtype: AudioData or AudioSource or list"""

        data = await self.http.putSource(
            list(map(lambda x: x.toDict(), source))
            if isinstance(source, list)
            else source.toDict()
        )

        return data["source"]

    async def loadSource(self, query):
        r"""Search the query and put source to the queue

        :param str query: The query to search.

        :rtype: AudioData or list"""

        data = await self.http.loadSource(query)

        return data["source"]

    async def skip(self, offset=1):
        r"""Skip the source

        :param int offset: how many to skip the sources"""

        return await self.http.skip(offset)

    async def seek(self, offset):
        r"""Seek the player

        :param float offset: The position to seek"""

        await self.http.seek(offset)

        await self.fetchState()

        return

    async def getOptions(self):
        r"""Get options of the player

        :rtype: dict"""

        return await self.http.getOptions()

    async def setOptions(self, **options):
        r"""Set options of the player

        :param Optional[float] volume: The volume of the player to change.
        :param Optional[float] crossfade: The crossfade of the player to change.
        :param Optional[bool] autoplay: The autoplay state of the player to change.
        :param Optional[dict] filter: The filter object of the player to change.

        :rtype: dict"""

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
        r"""Set volume of the player

        :param float volume: The volume of the player to change.

        :rtype: dict"""

        return await self.setOptions(volume=volume)

    async def setCrossfade(self, crossfade):
        r"""Set crossfade of the player

        :param float crossfade: The crossfade of the player to change.

        :rtype: dict"""

        return await self.setOptions(crossfade=crossfade)

    async def setAutoplay(self, autoplay):
        r"""Set autoplay state of the player

        :param bool autoplay: The autoplay state of the player to change.

        :rtype: dict"""

        return await self.setOptions(autoplay=autoplay)

    async def setFilter(self, filter):
        r"""Set filter of the player

        :param float crossfade: The filter object of the player to change.

        :rtype: dict"""

        return await self.setOptions(filter=filter)

    async def pause(self):
        r"""Pause the player"""

        await self.http.pause()

        await self.fetchState()

        return

    async def resume(self):
        r"""Resume the player"""

        await self.http.resume()

        await self.fetchState()

        return

    async def shuffle(self):
        r"""Shuffle the queue

        :rtype: list[AudioData or AudioSource]"""

        data = await self.http.shuffle()

        self.Queue.handleGetQueue(data)

        return self.Queue

    async def getCurrent(self):
        r"""Fetch current playing source

        :rtype: AudioSource"""

        self._current = await self.http.getCurrent()

        return self._current

    async def fetchState(self):
        r"""Fetch current player state.

        :rtype: dict"""

        data = await self.query("getState")

        return data

    async def fetchQueue(self, ws=True):
        r"""Fetch queue to force refresh the internal queue.

        :param Optional[bool] ws: Whether to request queue on websocket or not.

        :rtype: list[AudioData or AudioSource]"""

        if ws:
            await self.query("getQueue")
        else:
            self.Queue.handleGetQueue(await self.http.queue())

        return self.Queue

    async def requestSubtitle(self, lang=None, url=None):
        r"""Request to send synced subtitle to discodo node.

        One of the parameters is required.

        :param Optional[str] lang: The language to get subtitle.
        :param Optional[str] url: The subtitle url to fetch.

        :rtype: dict"""

        if not any([lang, url]):
            raise ValueError("Either `lang` or `url` is needed.")

        Data = {}
        if url:
            Data["url"] = url
        elif lang:
            Data["lang"] = lang

        return await self.query("requestSubtitle", Data)

    async def getSubtitle(self, *args, callback, **kwargs):
        r"""Request to send synced subtitle to discodo node and handle event to callback function.

        ``lang`` or ``url`` is required.

        :param callable callback: The callback function on subtitle event, must be coroutine function.
        :param Optional[str] lang: The language to get subtitle.
        :param Optional[str] url: The subtitle url to fetch.

        :rtype: dict"""

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
        r"""Move the player's current Node.

        :param discodo.Node node: The node to move to."""

        if node == self.Node:
            raise ValueError("Already connected to this node.")

        channel = self.client.client.get_channel(self.channel_id)

        if not channel:
            raise ValueError("this voice client is not connected to the channel.")

        await self.fetchState()

        VC = await self.client.connect(channel, node)

        await VC.setOptions(
            volume=self.volume,
            crossfade=self.crossfade,
            autoplay=self.autoplay,
            filter=self.filter,
        )

        if self.context:
            await VC.setContext(self.context)

        if self.current:
            await VC.putSource(self.current)

        if self.Queue:
            await VC.putSource(self.Queue)

        return VC

    async def destroy(self):
        r"""Destroy the client"""

        return await self.query("VC_DESTROY", event="VC_DESTROYED")
