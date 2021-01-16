import logging
import random
import re
from typing import Union

from youtube_related import RateLimited
from youtube_related import preventDuplication as relatedClient

from .config import Config
from .connector import VoiceConnector
from .errors import NotPlaying
from .player import Player
from .source import AudioData, AudioSource
from .utils import EventDispatcher

log = logging.getLogger("discodo.VoiceClient")

YOUTUBE_VIDEO_REGEX = re.compile(
    r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
)


class VoiceClient(VoiceConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.relatedClient = relatedClient()

        self.dispatcher = EventDispatcher()
        self.dispatcher.onAny(self.__dispatchToManager)
        self.dispatcher.on("REQUIRE_NEXT_SOURCE", self.__fetchAutoPlay)

        self.Context = {}

        self.Queue = []
        self.player = None

        self._filter = {}
        self.paused = False

        self._autoplay = Config.DEFAULT_AUTOPLAY
        self._crossfade = Config.DEFAULT_CROSSFADE

        self._volume = Config.DEFAULT_VOLUME

        self.dispatcher.dispatch("VC_CREATED", id=self.id)

    def __del__(self) -> None:
        guild_id = int(self.guild_id) if self.guild_id else None

        log.info(f"destroying voice client of {guild_id}.")

        if self.manager.voiceClients.get(guild_id) == self:
            self.dispatcher.dispatch("VC_DESTROYED")
            del self.manager.voiceClients[guild_id]

        super().__del__()

        if self.player and self.player.is_alive():
            self.player.stop()

        for Item in self.Queue:
            if isinstance(Item, AudioSource):
                self.loop.call_soon_threadsafe(Item.cleanup)

    def __repr__(self) -> str:
        return f"<VoiceClient guild_id={self.guild_id} volume={self.volume} crossfade={self.crossfade} autoplay={self.autoplay}>"

    def __dispatchToManager(self, event, *args, **kwargs) -> None:
        self.manager.dispatcher.dispatch(self.guild_id, *args, event=event, **kwargs)

    async def __fetchAutoPlay(self, current, **_):
        for _ in range(5):
            if self.autoplay and not self.Queue:
                if YOUTUBE_VIDEO_REGEX.match(current.webpage_url):
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

    def __spawnPlayer(self) -> None:
        if self.player and self.player.is_alive():
            return

        self.player = Player(self)
        self.player.crossfade = self.crossfade

        self.player.start()

    @property
    def channel_id(self) -> int:
        return self._channel_id

    @channel_id.setter
    def channel_id(self, value: int) -> None:
        self._channel_id = int(value)

        self.dispatcher.dispatch("VC_CHANNEL_EDITED", channel_id=self._channel_id)

    async def createSocket(self, data: dict = None) -> None:
        """
        Create UDP socket with discord to send voice packet.

        :param dict data: A VOICE_SERVER_UPDATE payload, defaults to None
        :rtype: None
        """

        await super().createSocket(data)

        self.__spawnPlayer()

    @property
    def state(self) -> str:
        """
        The current state of playback of the voice client

        :getter: Returns VoiceClient state
        :rtype: str
        """

        if not self.player:
            return "disconnected"
        elif not self.Queue and not self.player.current:
            return "stopped"
        elif self.paused:
            return "paused"
        else:
            return "playing"

    @property
    def volume(self) -> float:
        """
        Current volume of the voice client (0.0~2.0)

        :getter: Returns VoiceClient volume
        :setter: Set VoiceClient volume
        :rtype: float
        """

        return self._volume

    @volume.setter
    def volume(self, value: float) -> None:
        self._volume = round(max(value, 0.0), 2)

    @property
    def crossfade(self) -> float:
        """
        Current crossfade value of the voice client

        :getter: Returns VoiceClient crossfade
        :setter: Set VoiceClient crossfade
        :rtype: float
        """

        return self._crossfade

    @crossfade.setter
    def crossfade(self, value: float) -> None:
        if not isinstance(value, float):
            return TypeError("`crossfade` property must be `float`.")

        self.player.crossfade = self._crossfade = round(max(value, 0.0), 1)

    @property
    def autoplay(self) -> bool:
        """
        Current autoplay value of the voice client

        :getter: Returns VoiceClient autoplay
        :setter: Set VoiceClient autoplay
        :rtype: bool
        """

        return self._autoplay

    @autoplay.setter
    def autoplay(self, value: bool) -> None:
        if not isinstance(value, bool):
            return TypeError("`autoplay` property must be `bool`.")

        self._autoplay = value

    @property
    def filter(self) -> dict:
        """
        Current filter value of the voice client

        :getter: Returns VoiceClient filter
        :setter: Set VoiceClient filter
        :rtype: dict
        """

        return self._filter

    @filter.setter
    def filter(self, value: dict) -> None:
        if not isinstance(value, dict):
            return TypeError("`filter` property must be `dict`.")

        self._filter = value

    @property
    def current(self) -> Union[AudioSource, AudioData]:
        """
        Current source of the voice client

        :getter: Returns current source
        :rtype: :class:`AudioSource` or :class:`AudioData`
        """

        return self.player.current

    @property
    def next(self) -> Union[AudioSource, AudioData]:
        """
        Next source of the voice client

        :getter: Returns next source
        :rtype: :class:`AudioSource` or :class:`AudioData`
        """

        return self.player.next

    def putSource(self, Source: Union[list, AudioData, AudioSource]) -> int:
        """
        Put source to Queue.

        :param Source: list or :class:`AudioSource` or :class:`AudioData` to put on Queue
        :rtype: int
        """

        if not isinstance(Source, (list, AudioData, AudioSource)):
            raise TypeError("`Source` must be `list` or `AudioData` or `AudioSource`.")

        self.Queue += Source if isinstance(Source, list) else [Source]

        self.dispatcher.dispatch(
            "putSource", sources=(Source if isinstance(Source, list) else [Source])
        )

        return (
            self.Queue.index(Source)
            if not isinstance(Source, list)
            else [self.Queue.index(Item) for Item in Source]
        )

    async def getSource(self, Query: str) -> AudioData:
        """
        Get source from Query

        :param str Query: Query to search
        :rtype: :class:`AudioData`
        """

        return await AudioData.create(Query)

    async def loadSource(self, Query: str, **kwargs) -> AudioData:
        """
        Get source from Query and put it on Queue.

        :param str Query: Query to search
        :rtype: :class:`AudioData`
        """

        Data = await self.getSource(Query)

        if "related" in kwargs and isinstance(kwargs["related"], bool):
            Data.related = kwargs["related"]

        Index = self.putSource(Data)

        self.dispatcher.dispatch(
            "loadSource",
            source=(
                {"data": Data, "index": Index}
                if not isinstance(Data, list)
                else list(
                    map(
                        lambda zipped: {"data": zipped[0], "index": zipped[1]},
                        zip(Data, Index),
                    )
                )
            ),
            **kwargs,
        )

        return Data

    async def seek(self, offset: int) -> None:
        """
        Seek current playing source.

        :param float offset: offset to seek
        :rtype: None
        """

        return await self.player.seek(offset)

    def skip(self, offset: int = 1) -> None:
        """
        skip current playing source.

        :param float offset: offset to skip
        :rtype: None
        """

        if not self.player.current:
            raise NotPlaying

        if len(self.Queue) < (offset - 1):
            raise ValueError("`offset` is bigger than `Queue` size.")

        if offset > 1:
            del self.Queue[0 : (offset - 1)]

        self.player.current.skip()

    def pause(self) -> bool:
        """
        Pause playing

        :rtype: True
        """

        self.paused = True
        return True

    def resume(self) -> bool:
        """
        Resume playing

        :rtype: True
        """

        self.paused = False
        return False

    def shuffle(self) -> dict:
        """
        Shuffle Queue.

        :rtype: dict
        """

        if not self.Queue:
            raise ValueError("`Queue` is empty now.")

        random.shuffle(self.Queue)

        return self.Queue
