class _Config:
    __slots__ = [
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
    ]

    def __init__(self) -> None:
        # PLAYER
        self.DEFAULT_AUTOPLAY = True
        self.DEFAULT_VOLUME = 1.0
        self.DEFAULT_CROSSFADE = 10.0
        self.DEFAULT_GAPLESS = False

        # Audio
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

    @property
    def SAMPLES_PER_FRAME(self) -> int:
        return int(self.SAMPLING_RATE / 1000 * self.FRAME_LENGTH)

    @property
    def FRAME_SIZE(self) -> int:
        return self.SAMPLES_PER_FRAME ** 2

    @property
    def DELAY(self) -> float:
        return self.FRAME_LENGTH / 1000.0


Config = _Config()
