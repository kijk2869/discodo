import time
import audioop
import traceback
from ..natives import AudioFifo, Loader


class AudioSource:
    def __init__(self, file, volume=1.0, AudioData=None):
        self._volume = volume

        self.AudioFifo = AudioFifo()
        self.Loader = Loader(file, self.AudioFifo)
        self.Loader.start()

        self.AudioData = AudioData

        self.AVDurationLoaded = False

        self._duration = 0.0
        self.stopped = False

    def __del__(self):
        self.cleanup()

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = max(value, 0.0)

    @property
    def duration(self):
        return round(self._duration, 2)

    @property
    def remain(self):
        return round(self.AudioData.duration - self.duration, 2)

    def read(self):
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

        self._duration += 0.02
        self._duration = round(self._duration, 2)

        return Data

    def seek(self, offset):
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
