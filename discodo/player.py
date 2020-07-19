import os
import time
import audioop
import asyncio
import threading
import traceback
from .AudioSource import AudioData, AudioSource

PRELOAD_TIME = int(os.getenv('PRELOAD_TIME', '10'))
FRAME_LENGTH = int(os.getenv('FRAME_LENGTH', '20'))
DELAY = FRAME_LENGTH / 1000.0


class Player(threading.Thread):
    def __init__(self, voice_client, volume=1.0, loop=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self._end = threading.Event()
        self.loop = loop or asyncio.get_event_loop()

        self.client = voice_client
        self.speakState = False
        self.__next_called = False

        self._volume = volume

    @property
    def current(self) -> AudioSource:
        Source = self.client.Queue[0] if self.client.Queue else None
        if Source:
            if isinstance(Source, AudioData):
                Future = asyncio.run_coroutine_threadsafe(
                    Source.source(), self.loop)
                while not Future.done():
                    pass

                if self.client.Queue[0] == Source:
                    Source = self.client.Queue[0] = Future.result()

                if Source.volume != 1.0:
                    Source.volume = 1.0

                if not hasattr(Source, '_dispatched'):
                    Source._dispatched = True
                    self.client.event.dispatch(
                        'SongStart', song=Source.AudioData.toDict())
            elif isinstance(Source, AudioSource) and Source.filter != self.client.filter and hasattr(Source.Loader, 'selectAudioStream'):
                Source.filter = self.client.filter

        return Source

    @property
    def next(self) -> AudioSource:
        Source = self.client.Queue[1] if self.client.Queue and len(
            self.client.Queue) > 1 else None

        if Source and isinstance(Source, AudioSource):
            if not hasattr(Source, '_dispatched'):
                Source._dispatched = True
                self.client.event.dispatch(
                    'SongStart', song=Source.AudioData.toDict())
            if Source.filter != self.client.filter and hasattr(Source.Loader, 'selectAudioStream'):
                Source.filter = self.client.filter

        return Source

    def nextReady(self):
        self.loop.create_task(self._nextReady())

    async def _nextReady(self):
        Source = self.client.Queue[1] if self.client.Queue and len(
            self.client.Queue) > 1 else None
        if Source:
            if isinstance(Source, AudioData):
                Data = await Source.source()

                if self.client.Queue[1] == Source:
                    Source = self.client.Queue[1] = Data

                if Data.volume != 0.0:
                    Data.volume = 0.0
            elif isinstance(Source, AudioSource) and Source.filter != self.client.filter and hasattr(Source.Loader, 'selectAudioStream'):
                Source.filter = self.client.filter

    def makeFrame(self) -> bytes:
        if not self.current:
            return

        Data = self.current.read()

        if not Data or self.current.volume == 0.0:
            self.loop.call_soon_threadsafe(self.current.cleanup)
            self.client.event.dispatch(
                'SongEnd', song=self.current.AudioData.toDict())
            del self.client.Queue[0]
            self.speak(True)

        if self.next and (self.current.remain <= (PRELOAD_TIME + self.client.crossfade) or self.current.stopped):
            if self.__next_called:
                self.__next_called = False
            if isinstance(self.next, AudioData) and not hasattr(self.next, '_called'):
                self.next._called = True
                self.nextReady()
            elif self.client.crossfade and isinstance(self.next, AudioSource) and (self.current.remain <= self.client.crossfade or self.current.stopped):
                NextData = self.next.read()

                if NextData:
                    CrossFadeVolume = 1.0 / (self.client.crossfade / DELAY)
                    if self.next.volume < 1.0:
                        self.next.volume = round(
                            self.next.volume + CrossFadeVolume, 10)
                    if self.current.volume > 0.0:
                        self.current.volume = round(
                            self.current.volume - CrossFadeVolume, 10)

                    Data = audioop.add(Data, NextData, 2)
        elif not self.__next_called and (self.current.remain <= (PRELOAD_TIME + self.client.crossfade) or self.current.stopped):
            self.client.event.dispatch(
                'NeedNextSong', current=self.current.AudioData.toDict())
            self.__next_called = True
        elif self.current and self.current.stopped:
            if isinstance(self.current, AudioSource) and self.current.volume > 0.0:
                CrossFadeVolume = 1.0 / (self.client.crossfade / DELAY)
                self.current.volume = round(
                    self.current.volume - CrossFadeVolume, 10)
        else:
            if isinstance(self.current, AudioSource) and self.current.volume < 1.0:
                self.current.volume = round(self.current.volume + 0.01, 3)
            if isinstance(self.next, AudioSource) and self.next.volume != 0.0:
                self.next.volume = 0.0

        return Data

    def _do_run(self):
        self.loops = 0
        _start = time.perf_counter()

        while not self._end.is_set():
            try:
                if not self.client._connected.is_set():
                    while not self.client._connected.is_set():
                        pass
                    self.loops = 0
                    _start = time.perf_counter()

                Data = self.makeFrame()

                if self._volume != self.client.volume:
                    if self._volume < self.client.volume:
                        self._volume = round(self._volume + 0.01, 3)
                    if self._volume > self.client.volume:
                        self._volume = round(self._volume - 0.01, 3)

                if Data:
                    if not self.speakState:
                        self.speak(True)

                    if self._volume != 1.0:
                        Data = audioop.mul(Data, 2, min(self._volume, 2.0))

                    self.client.send(Data)
                elif self.speakState:
                    self.speak(False)

                self.loops += 1
                nextTime = _start + DELAY * self.loops
                time.sleep(max(0, DELAY + (nextTime - time.perf_counter())))
            except:
                traceback.print_exc()

    def run(self):
        try:
            self._do_run()
        finally:
            self.stop()

    def stop(self):
        self._end.set()
        self.speak(False)

    def speak(self, value):
        self.speakState = value
        asyncio.run_coroutine_threadsafe(
            self.client.ws.speak(value), self.client.loop)
