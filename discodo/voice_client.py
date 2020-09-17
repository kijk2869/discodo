from .utils import EventDispatcher
from .voice_connector import VoiceConnector
from .player import Player
from .config import Config
import logging
from .natives import AudioSource

log = logging.getLogger("discodo.VoiceClient")


class VoiceClient(VoiceConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.event = EventDispatcher()

        self.Queue = []
        self.player = None

        self._filter = {}
        self.paused = self._repeat = False

        self._volume = Config.DEFAULT_VOLUME

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

    def __spawnPlayer(self) -> None:
        if self.player and self.player.is_alive():
            return

        self.player = Player(self)
        self.player.crossfade = Config.DEFAULT_CROSSFADE
        self.player.gapless = Config.DEFAULT_GAPLESS

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

        self._crossfade = round(max(value, 0.0), 1)

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