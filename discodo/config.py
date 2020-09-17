class Config:
    __slots__ = [
        "SAMPLING_RATE",
        "CHANNELS",
        "FRAME_LENGTH",
        "SAMPLE_SIZE",
        "EXPECTED_PACKETLOSS",
        "BITRATE",
    ]

    def __init__(self) -> None:
        # Audio
        self.SAMPLING_RATE = 48000
        self.CHANNELS = 2
        self.FRAME_LENGTH = 20
        self.SAMPLE_SIZE = 4
        self.EXPECTED_PACKETLOSS = 0.0
        self.BITRATE = 128

        # BUFFER
        self.BUFFERLIMIT = 5
        self.PRELOAD_TIME = 10

    @property
    def SAMPLES_PER_FRAME(self) -> int:
        return int(self.SAMPLING_RATE / 1000 * self.FRAME_LENGTH)

    @property
    def FRAME_SIZE(self) -> int:
        return self.SAMPLES_PER_FRAME ** 2

    @property
    def DELAY(self) -> float:
        return self.FRAME_LENGTH / 1000.0


Config = Config()