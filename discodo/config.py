import uuid

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
        "DEFAULT_GAPLESS",
        "SAMPLING_RATE",
        "CHANNELS",
        "FRAME_LENGTH",
        "SAMPLE_SIZE",
        "EXPECTED_PACKETLOSS",
        "BITRATE",
        "BUFFERLIMIT",
        "PRELOAD_TIME",
        "VCTIMEOUT",
        "ENABLED_EXT_EXTRACTOR",
        "SPOTIFY_ID",
        "SPOTIFY_SECRET",
        "RANDOM_STATE",
    ]

    def __init__(self) -> None:
        # SERVER
        self.HOST = "0.0.0.0"
        self.PORT = 8000
        self.PASSWORD = "hellodiscodo"
        self.HANDSHAKE_INTERVAL = 15
        self.HANDSHAKE_TIMEOUT = 60.0

        # NETWORK
        self.IPBLOCKS = []
        self.EXCLUDEIPS = []

        # PLAYER
        self.DEFAULT_AUTOPLAY = True
        self.DEFAULT_VOLUME = 1.0
        self.DEFAULT_CROSSFADE = 10.0
        self.DEFAULT_GAPLESS = False

        # AUDIO
        self.SAMPLING_RATE = 48000
        self.CHANNELS = 2
        self.FRAME_LENGTH = 20
        self.SAMPLE_SIZE = 4
        self.EXPECTED_PACKETLOSS = 0
        self.BITRATE = 128

        # BUFFER
        self.BUFFERLIMIT = 5
        self.PRELOAD_TIME = 10

        # CONNECTION
        self.VCTIMEOUT = 300.0

        # EXTRA EXTRACTOR
        self.ENABLED_EXT_EXTRACTOR = ["melon", "spotify"]

        self.SPOTIFY_ID = None
        self.SPOTIFY_SECRET = None

        # ETC
        self.RANDOM_STATE = str(uuid.uuid4())

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
    def RoutePlanner(self) -> RoutePlanner:
        if not self.IPBLOCKS:
            return None

        if not hasattr(self, "_RoutePlanner"):
            self._RoutePlanner = RoutePlanner(self.IPBLOCKS, self.EXCLUDEIPS)

        return self._RoutePlanner

    def from_dict(self, data: dict) -> None:
        for Key, Value in data.items():
            setattr(self, Key, Value)


Config = _Config()
