import uuid
from typing import Union

from .planner import RoutePlanner


class _Config:
    __slots__ = [
        "HOST",
        "PORT",
        "PASSWORD",
        "HANDSHAKE_INTERVAL",
        "HANDSHAKE_TIMEOUT",
        "IPBLOCKS",
        "EXCLUDEIPS",
        "_RoutePlanner",
        "DEFAULT_AUTOPLAY",
        "DEFAULT_VOLUME",
        "DEFAULT_CROSSFADE",
        "SAMPLING_RATE",
        "CHANNELS",
        "FRAME_LENGTH",
        "SAMPLE_SIZE",
        "EXPECTED_PACKETLOSS",
        "BITRATE",
        "BUFFERLIMIT",
        "PRELOAD_TIME",
        "VCTIMEOUT",
        "ENABLED_EXT_RESOLVER",
        "PLAYLIST_PAGE_LIMIT",
        "SPOTIFY_ID",
        "SPOTIFY_SECRET",
        "RANDOM_STATE",
    ]

    def __init__(self) -> None:
        # SERVER
        self.HOST: str = "0.0.0.0"
        self.PORT: int = 8000
        self.PASSWORD: str = "hellodiscodo"
        self.HANDSHAKE_INTERVAL: str = 15
        self.HANDSHAKE_TIMEOUT: str = 60.0

        # NETWORK
        self.IPBLOCKS: list = []
        self.EXCLUDEIPS: list = []

        # PLAYER
        self.DEFAULT_AUTOPLAY: bool = True
        self.DEFAULT_VOLUME: float = 1.0
        self.DEFAULT_CROSSFADE: float = 10.0

        # AUDIO
        self.SAMPLING_RATE: int = 48000
        self.CHANNELS: int = 2
        self.FRAME_LENGTH: int = 60  # 2.5, 5, 10, 20, 40, 60
        self.SAMPLE_SIZE: int = 4
        self.EXPECTED_PACKETLOSS: int = 0
        self.BITRATE: int = 128

        # BUFFER
        self.BUFFERLIMIT: int = 5
        self.PRELOAD_TIME: int = 10

        # CONNECTION
        self.VCTIMEOUT: float = 300.0

        # EXTRA RESOLVER
        self.ENABLED_EXT_RESOLVER: list = []  # melon, spotify, vibe

        self.PLAYLIST_PAGE_LIMIT: int = 6

        self.SPOTIFY_ID: str = None
        self.SPOTIFY_SECRET: str = None

        # ETC
        self.RANDOM_STATE: str = str(uuid.uuid4())

    @property
    def SAMPLES_PER_FRAME(self) -> int:
        return int(self.SAMPLING_RATE / 1000 * self.FRAME_LENGTH)

    @property
    def FRAME_SIZE(self) -> int:
        return self.SAMPLES_PER_FRAME ** 2

    @property
    def DELAY(self) -> float:
        return self.FRAME_LENGTH / 1000.0

    @property
    def RoutePlanner(self) -> Union[None, RoutePlanner]:
        if not self.IPBLOCKS:
            return None

        if not hasattr(self, "_RoutePlanner"):
            self._RoutePlanner = RoutePlanner(self.IPBLOCKS, self.EXCLUDEIPS)

        return self._RoutePlanner

    def from_dict(self, data: dict) -> None:
        for Key, Value in data.items():
            setattr(self, Key, Value)


Config = _Config()
