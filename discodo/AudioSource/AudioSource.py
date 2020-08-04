import audioop
import os

from ..exceptions import AudioSourceNotPlaying, NotSeekable
from ..natives import AudioFifo, Loader

SAMPLING_RATE = int(os.getenv("SAMPLING_RATE", "48000"))
FRAME_LENGTH = int(os.getenv("FRAME_LENGTH", "20"))
SAMPLE_SIZE = int(os.getenv("SAMPLE_SIZE", "4"))
SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)


class AudioSource:
    def __init__(self, file, volume=1.0, AudioData=None):
        self._volume = volume

        self.AudioFifo = AudioFifo()
        self.Loader = Loader(file, self.AudioFifo)
        self.Loader.start()

        self.AudioData = AudioData

        self.AVDurationLoaded = False

        self._filter = {}
        self._filterGraph = None

        self._duration = 0.0
        self.stopped = False

    def __del__(self):
        self.cleanup()

    def __getattr__(self, name: str):
        return getattr(self.AudioData, name)

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(value, 0.0)

    @property
    def duration(self) -> float:
        return round(
            self.Loader.current
            - self.AudioFifo.samples
            / SAMPLES_PER_FRAME
            / 50
            / float(self._filter.get("atempo", "1.0")),
            2,
        )

    @property
    def remain(self) -> float:
        return round(self.AudioData.duration - self.duration, 2)

    @property
    def filter(self) -> dict:
        return self._filter

    @filter.setter
    def filter(self, value: dict):
        if self.AudioData.is_live and "atempo" in value:
            del value["atempo"]

        self._filter = value
        self.Loader.Filter = value

    def read(self) -> bytes:
        if not self.AudioFifo:
            return

        Data = self.AudioFifo.read()

        if not self.AVDurationLoaded and self.Loader and self.Loader.duration:
            self.AudioData.duration = self.Loader.duration
            self.AVDurationLoaded = True

        if not Data and self.Loader and self.Loader._buffering.locked():
            while self.Loader._buffering.locked():
                Data = self.AudioFifo.read()
                if Data:
                    break

        if Data and self.volume != 1.0:
            Data = audioop.mul(Data, 2, min(self._volume, 2.0))

        return Data

    def seek(self, offset: float):
        if self.AudioData.is_live:
            raise NotSeekable

        if not self.Loader:
            raise AudioSourceNotPlaying

        offset = (
            min(max(offset, 1), self.AudioData.duration - 1)
            if self.AudioData.duration
            else max(offset, 1)
        )
        self.Loader.seek(offset, any_frame=True)

    def stop(self):
        self.stopped = True
        return self.stopped

    def cleanup(self):
        self.Loader.stop()
        if self.AudioFifo and not self.AudioFifo.haveToFillBuffer.is_set():
            self.AudioFifo.haveToFillBuffer.set()
        self.AudioFifo = self.Loader.AudioFifo = None
