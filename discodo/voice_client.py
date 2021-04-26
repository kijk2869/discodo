import random
import re

from youtube_related import RateLimited
from youtube_related import preventDuplication as relatedClient

from .config import Config
from .connector import VoiceConnector
from .enums import PlayerState
from .errors import NotPlaying
from .player import Player
from .source import AudioData, AudioSource
from .utils import CallbackList, EventDispatcher


class DiscordVoiceClient(VoiceConnector):
    def __init__(self, manager, data=None):
        super().__init__(manager, data=data)

        self.relatedClient = relatedClient()

        self.dispatcher = EventDispatcher()
        self.dispatcher.onAny(
            lambda event, *args, **kwargs: manager.dispatcher.dispatch(
                self.guild_id, *args, event=event, **kwargs
            )
        )
        self.dispatcher.on("REQUIRE_NEXT_SOURCE", self.__fetchAutoPlay)

        self.Context = {}
        self.Queue = CallbackList()
        self.Queue.callback = self.__queueCallback

        self.player = None
        self.paused = False

        self.filter = {}
        self.autoplay = Config.DEFAULT_AUTOPLAY
        self._volume = Config.DEFAULT_VOLUME
        self._crossfade = Config.DEFAULT_CROSSFADE

    def __del__(self):
        guild_id = self.guild_id if self.guild_id else None

        if self.manager.voiceClients.get(guild_id) == self:
            self.dispatcher.dispatch("VC_DESTROYED")
            del self.manager.voiceClients[guild_id]

        super().__del__()

        if self.player and self.player.is_alive():
            self.player.stop()

        for Item in filter(lambda x: isinstance(x, AudioSource), self.Queue):
            self.loop.call_soon_threadsafe(Item.cleanup)

    def __repr__(self) -> str:
        return f"<VoiceClient guild_id={self.guild_id} volume={self.volume} crossfade={self.crossfade} autoplay={self.autoplay}>"

    async def __fetchAutoPlay(self, current, **_):
        if (
            self.autoplay
            and not self.Queue
            and re.match(
                r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$",
                current.webpage_url,
            )
        ):
            for _ in range(5):
                address = Config.RoutePlanner.get() if Config.RoutePlanner else None
                try:
                    Related = await self.relatedClient.async_get(
                        current.webpage_url, local_addr=address
                    )
                except RateLimited:
                    Config.RoutePlanner.mark_failed_address(address)
                else:
                    return await self.loadSource(
                        "https://www.youtube.com/watch?v=" + Related["id"],
                        related=True,
                    )

    def __queueCallback(self, name, *args):
        self.dispatcher.dispatch("QUEUE_EVENT", name=name, args=args)

    @property
    def channel_id(self):
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value) -> None:
        self._channel_id = value

        self.dispatcher.dispatch("VC_CHANNEL_EDITED", channel_id=self._channel_id)

    async def createSocket(self, data=None):
        await super().createSocket(data=data)

        if self.player and self.player.is_alive():
            return

        self.player = Player(self)
        self.player.start()

    @property
    def state(self):
        if not self.player:
            return PlayerState.DISCONNECTED
        elif not self.Queue and not self.player.current:
            return PlayerState.STOPPED
        elif self.paused:
            return PlayerState.PAUSED
        else:
            return PlayerState.PLAYING

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = round(max(value, 0.0), 2)

    @property
    def crossfade(self) -> float:
        return self._crossfade

    @crossfade.setter
    def crossfade(self, value: float):
        self._crossfade = round(max(value, 0.0), 1)

    @property
    def current(self):
        if not self.player:
            return

        return self.player.current

    @property
    def next(self):
        if not self.player:
            return

        return self.player.next

    async def getSource(self, query):
        return await AudioData.create(query)

    def putSource(self, source):
        sources = source if isinstance(source, list) else [source]

        self.Queue.extend(sources)

        self.dispatcher.dispatch("putSource", sources=sources)

        return (
            self.Queue.index(source)
            if not isinstance(source, list)
            else list(map(self.Queue.index, sources))
        )

    async def loadSource(self, query, **kwargs):
        source = await self.getSource(query)

        if isinstance(kwargs.get("related"), bool):
            source.related = kwargs["related"]

        self.putSource(source)

        self.dispatcher.dispatch("loadSource", source=source, **kwargs)

        return source

    async def seek(self, offset):
        return await self.player.seek(offset)

    def skip(self, offset=1):
        if not self.player.current:
            raise NotPlaying

        if len(self.Queue) < (offset - 1):
            raise ValueError("`offset` is bigger than `Queue` size.")

        if offset > 1:
            del self.Queue[0 : (offset - 1)]

        self.player.current.skip()

    def pause(self):
        self.paused = True

        return self.paused

    def resume(self):
        self.paused = False

        return self.paused

    def shuffle(self):
        if not self.Queue:
            raise ValueError("`Queue` is empty now.")

        random.shuffle(self.Queue)
