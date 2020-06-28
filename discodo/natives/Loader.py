import av
import os
import threading
from ..utils.threadLock import withLock
import traceback

AVOption = {
    'reconnect': '1',
    'reconnect_streamed': '1',
    'reconnect_delay_max': '5'
}

SAMPLING_RATE = os.getenv('SAMPLING_RATE', 48000)
CHANNELS = os.getenv('CHANNELS', 2)


class Loader(threading.Thread):
    def __init__(self, Source: str, AudioFifo: av.AudioFifo):
        threading.Thread.__init__(self)
        self.daemon = True
        self.Source = Source

        self._end = threading.Event()
        self._buffering = threading.Lock()

        self.StreamConainer = None
        self.Resampler = av.AudioResampler(
            format=av.AudioFormat('s16').packed,
            layout='stereo' if CHANNELS >= 2 else 'mono',
            rate=SAMPLING_RATE
        )
        self.AudioFifo = AudioFifo

    def _do_run(self):
        if not self.StreamConainer:
            self.StreamConainer = av.open(self.Source, options=AVOption)

        self.FrameGenerator = self.StreamConainer.decode(audio=0)

        with withLock(self._buffering):
            while not self._end.is_set():
                Frame = next(self.FrameGenerator, None)
                if not Frame:
                    self.stop()
                    break
                
                if not self.AudioFifo.haveToFillBuffer.is_set():
                    self.AudioFifo.haveToFillBuffer.wait()

                Frame.pts = None
                Frame = self.Resampler.resample(Frame)
                self.AudioFifo.write(Frame)

    def run(self):
        try:
            self._do_run()
        finally:
            self.stop()

    def reload(self):
        if self.StreamConainer:
            self.FrameGenerator = self.StreamConainer.decode(audio=0)

        self.AudioFifo.reset()

        if not self._buffering.locked():
            self.start()

    def stop(self):
        self._end.set()
        if self.StreamConainer:
            self.StreamConainer.close()
            self.StreamConainer = None
