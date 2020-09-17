from .voice_connector import VoiceConnector
from .player import Player
from .config import Config
import logging
from .natives import AudioSource

log = logging.getLogger("discodo.VoiceClient")


class VoiceClient(VoiceConnector):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.Queue = []
        self.player = None

        self._filter = {}
        self.paused = self._repeat = False

        self._volume = Config.DEFAULT_VOLUME

    def __del__(self) -> None:
        guild_id = int(self.guild_id) if self.guild_id else None

        log.info(f"destroying voice client of {guild_id}.")

        if self.manager.voiceClients.get(guild_id) == self:
            # EVENT: VOICE CLIENT DESTROYED
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