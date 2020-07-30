import os
import random
from logging import getLogger

from youtube_related import preventDuplication as relatedClient

from .AudioSource import AudioData, AudioSource
from .player import Player
from .utils import EventEmitter
from .voice_connector import VoiceConnector

log = getLogger("discodo.VoiceClient")

DEFAULTVOLUME = float(os.getenv("DEFAULTVOLUME", "1.0"))
DEFAULTCROSSFADE = float(os.getenv("DEFAULTCROSSFADE", "10.0"))
DEFAULAUTOPLAY = True if os.getenv("DEFAULAUTOPLAY", "1") == "1" else False


class VoiceClient(VoiceConnector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.relatedClient = relatedClient()

        self.event = EventEmitter()
        self.event.onAny(self.onAnyEvent)
        self.event.on("NeedNextSong", self.getNext)
        self.event.on("SongEnd", self.getNext)

        self.InternalQueue = []
        self._filter = {}

        self.player = None
        self.paused = False
        self._repeat = False

        self.autoplay = DEFAULAUTOPLAY
        self._volume = DEFAULTVOLUME
        self._crossfade = DEFAULTCROSSFADE

        self.event.dispatch("VC_CREATED")

    @property
    def Queue(self):
        """Read only, if you want to edit queue use InternalQueue."""
        return (
            self.InternalQueue[1:]
            if self.InternalQueue and len(self.InternalQueue) > 1
            else []
        )

    def onAnyEvent(self, event, *args, **kwargs):
        self.client.event.dispatch(self.guild_id, event, *args, **kwargs)

    async def getNext(self, **kwargs):
        current = list(kwargs.values()).pop()

        if self.repeat:
            self.InternalQueue.append(await self.getSong(current["webpage_url"]))

        if self.autoplay and (
            not self.InternalQueue
            or (
                self.InternalQueue[0].toDict() == current
                and len(self.InternalQueue) <= 1
            )
        ):
            Related = await self.relatedClient.async_get(current["webpage_url"])
            await self.loadSong(Related["id"])

    def __del__(self):
        guild_id = int(self.guild_id) if self.guild_id else None

        log.info(f"destroying voice client of {guild_id}.")

        self.event.dispatch("VC_DESTROYED")

        if self.client.voiceClients.get(guild_id) == self:
            del self.client.voiceClients[guild_id]

        super().__del__()

        if self.player and self.player.is_alive():
            self.player.stop()

        for Item in self.InternalQueue:
            if isinstance(Item, AudioSource):
                self.loop.call_soon_threadsafe(Item.cleanup)

    async def createSocket(self, data: dict = None):
        await super().createSocket(data)

        if not self.player:
            self.player = Player(self)
            self.player.start()
        else:
            await self.ws.speak(True)

    def putSong(self, Data: AudioData) -> int:
        if not isinstance(Data, (list, AudioData, AudioSource)):
            raise ValueError

        if not isinstance(Data, list):
            Data = [Data]

        for Item in Data:
            self.InternalQueue.append(Item)

        self.event.dispatch(
            "putSong",
            songs=[
                dict(Item.toDict(), index=self.InternalQueue.index(Item))
                for Item in Data
            ],
        )

        return (
            self.InternalQueue.index(Data[0])
            if len(Data) == 1
            else [self.InternalQueue.index(Item) for Item in Data]
        )

    async def loadSong(self, Query: str) -> AudioData:
        Data = await AudioData.create(Query) if isinstance(Query, str) else Query

        self.event.dispatch(
            "loadSong",
            song=(
                [Item.toDict() for Item in Data]
                if isinstance(Data, list)
                else Data.toDict()
            ),
        )

        self.putSong(Data)

        return Data

    def seek(self, offset: int):
        if not self.player.current:
            raise ValueError

        self.player.current.seek(offset)

    def skip(self, offset: int = 1):
        if not self.player.current:
            raise ValueError

        if len(self.InternalQueue) < offset:
            raise ValueError

        del self.InternalQueue[1 : (offset - 1)]

        self.player.current.stop()

    def pause(self) -> bool:
        self.paused = True
        return self.paused

    def resume(self) -> bool:
        self.paused = False
        return self.paused

    def changePause(self) -> bool:
        if self.paused:
            return self.resume()
        else:
            return self.pause()

    def shuffle(self):
        if not self.InternalQueue:
            raise ValueError

        self.InternalQueue = self.InternalQueue[:1] + random.sample(
            self.Queue, k=len(self.Queue)
        )
        return self.Queue

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
    def filter(self) -> dict:
        return self._filter

    @filter.setter
    def filter(self, value: dict):
        self._filter = value

    @property
    def state(self) -> str:
        if not self.InternalQueue:
            return "stopped"
        if self.paused:
            return "paused"
        return "playing"

    @property
    def repeat(self) -> bool:
        return self._repeat

    @repeat.setter
    def repeat(self, value: bool):
        self._repeat = value
