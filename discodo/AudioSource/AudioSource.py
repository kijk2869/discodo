import time
import audioop
import traceback
from typing import Any
from ..natives import AudioFifo, Loader, AudioFilter


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

    # def __getattribute__(self, name: str) -> Any:
    #    return getattr(self.AudioData, name)

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = max(value, 0.0)

    @property
    def duration(self) -> float:
        return round(self._duration, 2)

    @property
    def remain(self) -> float:
        return round(self.AudioData.duration - self.duration, 2)

    @property
    def filter(self) -> dict:
        return self._filter

    @filter.setter
    def filter(self, value: dict):
        self._filter = value

        if value:
            self._filterGraph = AudioFilter()

            self._filterGraph.selectAudioStream = self.Loader.selectAudioStream
            self._filterGraph.setFilters(value)
        else:
            self._filterGraph = None

        self.Loader.FilterGraph = self._filterGraph
        self.seek(round(self.duration))

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

        self._duration += 0.02 * float(self._filter.get('atempo', '1.0'))
        self._duration = round(self._duration, 2)

        return Data

    def seek(self, offset: int):
        if not self.Loader:
            raise ValueError

        offset = min(max(offset, 1), self.AudioData.duration -
                     1) if self.AudioData.duration else max(offset, 1)
        self.Loader.seek(offset * 1000000, any_frame=True)
        self._duration = offset

    def stop(self):
        self.stopped = True
        return self.stopped

    def cleanup(self):
        self.Loader.stop()
        self.AudioFifo = None
