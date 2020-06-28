from ..natives import AudioFifo, Loader

class AudioSource:
    def __init__(self, file):
        self.AudioFifo = AudioFifo()
        self.Loader = Loader(file)
        self.Loader.start()
    
    def read(self):
        Data = self.AudioFifo.read()

        if not Data and self.Loader.locked():
            return self.read()

        return Data

    def cleanup(self):
        self.Loader.stop()
        self.AudioFifo = None