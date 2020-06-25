import av
import os

SAMPLING_RATE = os.getenv('SAMPLING_RATE', 48000)
FRAME_LENGTH = os.getenv('FRAME_LENGTH', 20)
SAMPLE_SIZE = os.getenv('SAMPLE_SIZE', 4)
SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)

AUDIOBUFFERLIMIT = os.getenv('AUDIOBUFFERLIMIT', 30)
AUDIOBUFFERLIMITMS = AUDIOBUFFERLIMIT * 1000 * SAMPLES_PER_FRAME

class AudioFifo(av.AudioFifo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def haveToFillBuffer(self):
        return self.samples < AUDIOBUFFERLIMITMS

    def read(self, samples=SAMPLES_PER_FRAME):
        AudioFrame = super().read(samples)
        if not AudioFrame:
            return

        return AudioFrame.planes[0].to_bytes()

    def reset(self):
        self.ptr = None
