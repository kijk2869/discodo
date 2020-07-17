import av
import os
import threading
from ..utils.threadLock import withLock

AVOption = {
    'err_detect': 'ignore_err',
    'reconnect': '1',
    'reconnect_streamed': '1',
    'reconnect_delay_max': '5'
}

SAMPLING_RATE = os.getenv('SAMPLING_RATE', 48000)
CHANNELS = os.getenv('CHANNELS', 2)


class Loader:
    def __init__(self, Source: str, AudioFifo: av.AudioFifo):
        self.Source = Source

        self._end = threading.Event()
        self._haveToReloadResampler = threading.Event()
        self._buffering = threading.Lock()

        self.StreamConainer = None
        self.FilterGraph = None
        self.reloadResampler()
        self.AudioFifo = AudioFifo

    def start(self):
        self.BufferLoader = BufferLoader(self)
        self.BufferLoader.start()

    @property
    def duration(self) -> float:
        return round(self.StreamConainer.duration / 1000000) if self.StreamConainer else None

    def seek(self, offset: float, *args, **kwargs):
        if not self.StreamConainer and not self._buffering.locked():
            self.StreamConainer = av.open(self.Source, options=AVOption)
        elif not self.StreamConainer:
            while not self.StreamConainer:
                pass

        self.StreamConainer.seek(offset, *args, **kwargs)
        self.reload()

    def reload(self):
        self.reloadResampler()

        if not self._buffering.locked():
            if self._end.is_set():
                self._end.clear()
            self.start()

        self.AudioFifo.reset()

    def reloadResampler(self):
        self._haveToReloadResampler.set()

    def stop(self):
        self._end.set()
        if self.StreamConainer:
            self.StreamConainer.close()
            self.StreamConainer = None


class BufferLoader(threading.Thread):
    def __init__(self, Loader):
        threading.Thread.__init__(self)
        self.daemon = True

        self.Loader = Loader
        self.Resampler = None
        self._PreviousFilter = None

    def _do_run(self):
        with withLock(self.Loader._buffering):
            if not self.Loader.StreamConainer:
                self.Loader.StreamConainer = av.open(
                    self.Loader.Source, options=AVOption)

            self.Loader.selectAudioStream = self.Loader.StreamConainer.streams.audio[0]
            self.Loader.FrameGenerator = self.Loader.StreamConainer.decode(
                audio=0)

            while not self.Loader._end.is_set():
                if self.Loader.FilterGraph and self._PreviousFilter != self.Loader.FilterGraph:
                    self.Loader.reloadResampler()
                    self._PreviousFilter = self.Loader.FilterGraph

                if not self.Resampler or self.Loader._haveToReloadResampler.is_set():
                    self.Resampler = av.AudioResampler(
                        format=av.AudioFormat('s16').packed,
                        layout='stereo' if CHANNELS >= 2 else 'mono',
                        rate=SAMPLING_RATE
                    )
                    self.Loader._haveToReloadResampler.clear()

                Frame = next(self.Loader.FrameGenerator, None)
                if not Frame:
                    self.Loader.stop()
                    break

                if self.Loader.FilterGraph:
                    if self._PreviousFilter != self.Loader.FilterGraph:
                        self.Loader.reloadResampler()
                        self._PreviousFilter = self.Loader.FilterGraph

                    self.Loader.FilterGraph.push(Frame)
                    Frame = self.Loader.FilterGraph.pull()

                    if not Frame:
                        continue

                Frame.pts = None
                Frame = self.Resampler.resample(Frame)

                if not self.Loader.AudioFifo.haveToFillBuffer.is_set():
                    self.Loader.AudioFifo.haveToFillBuffer.wait()

                self.Loader.AudioFifo.write(Frame)

    def run(self):
        try:
            self._do_run()
        finally:
            self.Loader.stop()
