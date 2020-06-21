import av
import threading
from ..utils.threadLock import withLock

AVOption = {
    'reconnect': '1',
    'reconnect_at_eof': '1',
    'reconnect_streamed': '1',
    'reconnect_delay_max': '5'
}


class Loader(threading.Thread):
    def __init__(self, Source: str, AudioFifo: av.AudioFifo):
        self.daemon = True
        self.Source = Source

        self._end = threading.Event()
        self._buffering = threading.Lock()

        self.StreamConainer = None
        self.Resampler = av.AudioResampler(
            format=av.AudioFormat('s16').packed,
            layout='stereo',
            rate=48000
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

                Frame.pts = None
                Frame = self.Resampler.resample(Frame)
                self.AudioFifo.write(Frame)

    def run(self):
        try:
            self.do_run()
        finally:
            self.stop()

    def reload(self):
        if not self.StreamConainer:
            return

        self.FrameGenerator = self.StreamConainer.decode(audio=0)
        self.AudioFifo.reset()

    def stop(self):
        self._end.set()
        if self.StreamConainer:
            self.StreamConainer.close()
