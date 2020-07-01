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
        self._volume = max(value, 0.0)
