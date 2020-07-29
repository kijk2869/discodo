import os
import threading

import av

SAMPLING_RATE = int(os.getenv("SAMPLING_RATE", "48000"))
FRAME_LENGTH = int(os.getenv("FRAME_LENGTH", "20"))
SAMPLE_SIZE = int(os.getenv("SAMPLE_SIZE", "4"))
SAMPLES_PER_FRAME = int(SAMPLING_RATE / 1000 * FRAME_LENGTH)

AUDIOBUFFERLIMIT = int(os.getenv("AUDIOBUFFERLIMIT", "5"))
AUDIOBUFFERLIMITMS = AUDIOBUFFERLIMIT * 50 * SAMPLES_PER_FRAME


class AudioFifo(av.AudioFifo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.haveToFillBuffer = threading.Event()
        self.haveToFillBuffer.set()

    def read(self, samples: int = SAMPLES_PER_FRAME) -> bytes:
        AudioFrame = super().read(samples)
        if not AudioFrame:
            return

        if self.samples < AUDIOBUFFERLIMITMS:
            self.haveToFillBuffer.set()
        else:
            self.haveToFillBuffer.clear()

        return AudioFrame.planes[0].to_bytes()

    def write(self, *args, **kwargs):
        super().write(*args, **kwargs)

        if self.samples < AUDIOBUFFERLIMITMS:
            self.haveToFillBuffer.set()
        else:
            self.haveToFillBuffer.clear()

    def reset(self):
        super().read(samples=max(self.samples - 960, 0), partial=True)
