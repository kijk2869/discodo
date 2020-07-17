import os
from logging import getLogger
from .player import Player
from .voice_connector import VoiceConnector
from .AudioSource import AudioData, AudioSource
from .utils import EventEmitter

log = getLogger('discodo.VoiceClient')

DEFAULTVOLUME = os.getenv('DEFAULTVOLUME', 1.0)
DEFAULTCROSSFADE = os.getenv('DEFAULTCROSSFADE', 10.0)


class VoiceClient(VoiceConnector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.event = EventEmitter()
        self.event.onAny(self.onAnyEvent)

        self.Queue = []
        self._filter = {}

        self.player = None

        self._volume = DEFAULTVOLUME
        self._crossfade = DEFAULTCROSSFADE

    def onAnyEvent(self, event, *args, **kwargs):
        self.client.event.dispatch(self.guild_id, event, *args, **kwargs)

    def __del__(self):
        guild_id = int(self.guild_id) if self.guild_id else None

        log.info(f'destroying voice client of {guild_id}.')

        if self.client.voiceClients.get(guild_id) == self:
            del self.client.voiceClients[guild_id]

        super().__del__()

        if self.player and self.player.is_alive():
            self.player.stop()

        for Item in self.Queue:
            if isinstance(Item, AudioSource):
                Item.cleanup()

    async def createSocket(self, *args, **kwargs):
        await super().createSocket(*args, **kwargs)

        if not self.player:
            self.player = Player(self)
            self.player.start()
        else:
            await self.ws.speak(True)

    def putSong(self, Data: AudioData) -> int:
        if not isinstance(Data, (AudioData, AudioSource)):
            raise ValueError
        
        if not isinstance(Data, list):
            Data = [Data]
        
        for Item in Data:
            self.Queue.append(Item)

        self.event.dispatch('putSong', songs=[dict(Item.toDict(), index=self.Queue.index(Item)) for Item in Data])

        return self.Queue.index(Data)

    async def loadSong(self, Query: str) -> AudioData:
        Data = await AudioData.create(Query) if isinstance(Query, str) else Query

        self.putSong(Data)

        return Data

    def seek(self, offset: int):
        if not self.player.current:
            raise ValueError

        self.player.current.seek(offset)

    def skip(self, offset: int = 1):
        if not self.player.current:
            raise ValueError

        if len(self.Queue) < offset:
            raise ValueError

        del self.Queue[1:(offset-1)]

        self.player.current.stop()

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
