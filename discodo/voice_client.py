import logging
import random
import re
from typing import Union

from youtube_related import preventDuplication as relatedClient

from .config import Config
from .errors import NotPlaying
from .player import Player
from .source import AudioData, AudioSource
from .utils import EventDispatcher
from .voice_connector import VoiceConnector

log = logging.getLogger("discodo.VoiceClient")


class VoiceClient(VoiceConnector):
    YOUTUBE_VIDEO_REGEX = re.compile(
        r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.relatedClient = relatedClient()

        self.event = EventDispatcher()
        self.event.onAny(self.__dispatchToManager)
        self.event.on("REQUIRE_NEXT_SOURCE", self.__fetchAutoPlay)

        self.Queue = []
        self.player = None

        self._filter = {}
        self.paused = self._repeat = False

        self._autoplay = Config.DEFAULT_AUTOPLAY
        self._crossfade = Config.DEFAULT_CROSSFADE
        self._gapless = Config.DEFAULT_GAPLESS

        self._volume = Config.DEFAULT_VOLUME

        self.event.dispatch("VC_CREATED")

    def __del__(self) -> None:
        guild_id = int(self.guild_id) if self.guild_id else None

        log.info(f"destroying voice client of {guild_id}.")

        if self.manager.voiceClients.get(guild_id) == self:
            self.event.dispatch("VC_DESTROYED")
            del self.manager.voiceClients[guild_id]

        super().__del__()

        if self.player and self.player.is_alive():
            self.player.stop()

        for Item in self.Queue:
            if isinstance(Item, AudioSource):
                self.loop.call_soon_threadsafe(Item.cleanup)

    def __repr__(self) -> str:
        return f"<VoiceClient guild_id={self.guild_id} volume={self.volume} crossfade={self.crossfade} autoplay={self.autoplay} gapless={self.gapless}>"

    def __dispatchToManager(self, event, *args, **kwargs) -> None:
        self.manager.event.dispatch(self.guild_id, *args, event=event, **kwargs)

    async def __fetchAutoPlay(self, **kwargs):
        current = list(kwargs.values()).pop()

        if self.autoplay and not self.Queue:
            if self.YOUTUBE_VIDEO_REGEX.match(current.webpage_url):
                Related = await self.relatedClient.async_get(current.webpage_url)

                await self.loadSource(Related["id"], related=True)

    def __spawnPlayer(self) -> None:
        if self.player and self.player.is_alive():
            return

        self.player = Player(self)
        self.player.crossfade = self._crossfade
        self.player.gapless = self._gapless

        self.player.start()

    async def createSocket(self, data: dict = None) -> None:
        await super().createSocket(data)

        self.__spawnPlayer()

    @property
    def state(self) -> str:
        if not self.Queue and not self.player.current:
            return "stopped"
        elif self.paused:
            return "paused"
        else:
            return "playing"

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = round(max(value, 0.0), 2)

    @property
    def crossfade(self) -> float:
        return self._crossfade

    @crossfade.setter
    def crossfade(self, value: float) -> None:
        if not isinstance(value, float):
            return TypeError("`filter` property must be `float`.")

        self.player.crossfade = self._crossfade = round(max(value, 0.0), 1)

    @property
    def gapless(self) -> bool:
        return self._gapless

    @gapless.setter
    def gapless(self, value: bool) -> None:
        if not isinstance(value, bool):
            return TypeError("`gapless` property must be `bool`.")

        self.player.gapless = self._gapless = self._gapless

    @property
    def autoplay(self) -> bool:
        return self._autoplay

    @autoplay.setter
    def autoplay(self, value: bool) -> None:
        if not isinstance(value, bool):
            return TypeError("`autoplay` property must be `bool`.")

        self._autoplay = value

    @property
    def filter(self) -> dict:
        return self._filter

    @filter.setter
    def filter(self, value: dict) -> None:
        if not isinstance(value, dict):
            return TypeError("`filter` property must be `dict`.")

        self._filter = value

    @property
    def repeat(self) -> bool:
        return self._repeat

    @repeat.setter
    def repeat(self, value: bool) -> None:
        if not isinstance(value, bool):
            return TypeError("`repeat` property must be `bool`.")

        self._repeat = value

    @property
    def current(self) -> Union[AudioSource, AudioData]:
        return self.player.current

    @property
    def next(self) -> Union[AudioSource, AudioData]:
        return self.player.next

    def putSource(self, Source: Union[list, AudioData, AudioSource]) -> int:
        if not isinstance(Source, (list, AudioData, AudioSource)):
            raise TypeError("`Source` must be `list` or `AudioData` or `AudioSource`.")

        self.Queue += Source if isinstance(Source, list) else [Source]

        self.event.dispatch(
            "putSource", sources=(Source if isinstance(Source, list) else [Source])
        )

        return (
            self.Queue.index(Source)
            if not isinstance(Source, list)
            else [self.Queue.index(Item) for Item in Source]
        )

    async def getSource(self, Query: str) -> AudioData:
        return await AudioData.create(Query)

    async def loadSource(self, Query: str, **kwargs) -> AudioData:
        Data = await self.getSource(Query)

        self.event.dispatch(
            "loadSource", source=(Data if isinstance(Data, list) else Data), **kwargs
        )

        self.putSource(Data)

        return Data

    async def seek(self, offset: int) -> None:
        return await self.player.seek(offset)

    def skip(self, offset: int = 1) -> None:
        if not self.player.current:
            raise NotPlaying

        if len(self.Queue) < (offset - 1):
            raise ValueError("`offset` is bigger than `Queue` size.")

        if offset > 1:
            del self.Queue[0 : (offset - 1)]

        self.player.current.stop()

    def pause(self) -> bool:
        self.paused = True
        return True

    def resume(self) -> bool:
        self.paused = False
        return False

    def shuffle(self) -> dict:
        if not self.Queue:
            raise ValueError("`Queue` is empty now.")

        random.shuffle(self.Queue)

        return self.Queue
