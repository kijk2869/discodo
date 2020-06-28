import audioop
import traceback
from ..natives import AudioFifo, Loader


class AudioSource:
    def __init__(self, file, volume=1.0, AudioData=None):
        self._volume = volume

        self.AudioFifo = AudioFifo()
        self.Loader = Loader(file)
        self.Loader.start()

        self.AudioData = AudioData

        self.AVDurationLoaded = False

        self._duration = 0.0

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = max(value, 0.0)
    
    @property
    def duration(self):
        return round(self._duration, 2)

    def read(self):
        Data = self.AudioFifo.read()

        if not self.AVDurationLoaded:
            self.AudioData.duration = self.Loader.duration
            self.AVDurationLoaded = True

        if not Data and self.Loader.locked():
            return self.read()

        if Data and self.volume != 1.0:
            Data = audioop.mul(Data, 2, min(self._volume, 2.0))
        
        self._duration += 0.02
        self._duration = round(self._duration, 2)

        return Data

    def cleanup(self):
        self.Loader.stop()
        self.AudioFifo = None
