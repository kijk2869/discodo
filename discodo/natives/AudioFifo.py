from av import AudioFifo

class AudioFifo(AudioFifo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def read(self, samples=20):
        return self.read(samples)
    
    def clear(self):
        raise NotImplementedError