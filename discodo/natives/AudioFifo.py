import threading

import av

from ..config import Config
import logging

log = logging.getLogger("discodo.natives.AudioFifo")


class AudioFifo(av.AudioFifo):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.AUDIOBUFFERLIMITMS = Config.BUFFERLIMIT * 50 * 960

        self.haveToFillBuffer = threading.Event()
        self.haveToFillBuffer.set()

    def check_buffer(self) -> None:
        if self.samples < self.AUDIOBUFFERLIMITMS:
            self.haveToFillBuffer.set()
        else:
            self.haveToFillBuffer.clear()

    def read(self, samples: int = 960) -> bytes:
        AudioFrame = super().read(samples)
        if not AudioFrame:
            return

        self.check_buffer()

        return AudioFrame.planes[0].to_bytes()

    def write(self, *args, **kwargs) -> None:
        try:
            super().write(*args, **kwargs)
        except:
            log.warning("while writing on fifo, an error occured, ignored.")

        self.check_buffer()

    def reset(self) -> None:
        super().read(samples=max(self.samples - 960, 0), partial=True)
