from logging import getLogger
from .player import Player
from .voice_connector import VoiceConnector
from .AudioSource import AudioData

log = getLogger('discodo.VoiceClient')


class VoiceClient(VoiceConnector):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.player = None

        self._volume = 1.0
        self._crossfade = 20.0

    async def createSocket(self, *args, **kwargs):
        await super().createSocket(*args, **kwargs)

        if not self.player:
            self.player = Player(self)
            self.player.start()
        else:
            await self.ws.speak(True)

    async def loadSong(self, Query):
        Data = await AudioData.create(Query) if isinstance(Query, str) else Query

        AddingData = [Data] if not isinstance(Data, list) else Data

        for Item in AddingData:
            self.player.add(Item)

        return Data

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = round(max(value, 0.0), 2)

    @property
    def crossfade(self):
        return self._crossfade

    @crossfade.setter
    def crossfade(self, value):
        self._crossfade = round(max(value, 0.0), 1)
