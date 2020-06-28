import audioop
import traceback
from ..natives import AudioFifo, Loader


class AudioSource:
    def __init__(self, file, volume=1.0):
        self._volume = volume

        self.AudioFifo = AudioFifo()
        self.Loader = Loader(file)
        self.Loader.start()
    
    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = max(value, 0.0)
    
    def read(self):
        Data = self.AudioFifo.read()

        if not Data and self.Loader.locked():
            return self.read()
        
        if Data and self.volume != 1.0:
            Data = audioop.mul(Data, 2, min(self._volume, 2.0))

        return Data

    def cleanup(self):
        self.Loader.stop()
        self.AudioFifo = None
