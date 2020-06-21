import av
import os

AUDIOBUFFERLIMIT = os.getenv('AUDIOBUFFERLIMIT', 30)
AUDIOBUFFERLIMITMS = AUDIOBUFFERLIMIT * 1000

class AudioFifo(av.AudioFifo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    @property
    def haveToFillBuffer(self):
        return self.samples < AUDIOBUFFERLIMITMS

    def read(self, samples=20):
        AudioFrame = super().read(samples)
        if not AudioFrame: return

        return AudioFrame.planes[0].to_bytes()

    def reset(self):
        self.ptr = None
