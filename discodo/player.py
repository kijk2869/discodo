import asyncio
import audioop
import threading
from typing import Callable, Union
from .natives import AudioSource, AudioData
from .config import Config
import time
import traceback


class Player(threading.Thread):
    def __init__(self, client) -> None:
        threading.Thread.__init__(self)
        self.daemon = True

        self.client = client

        self._volume = 1.0
        self._crossfade = 5.0
        self._gapless = False
        self._end = threading.Event()

        self._getSourceTask = None
        self._current = self._next = None

        self._crossfadeLoop = 0
        self.haveToLoadNext = False

    def __del__(self) -> None:
        for Source in self.client.Queue:
            if isinstance(Source, AudioSource):
                self.client.loop.run_coroutine_threadsafe(Source.cleanup)

    @property
    def crossfade(self) -> Union[float, None]:
        if self._gapless:
            return None

        return self._crossfade

    @crossfade.setter
    def crossfade(self, value: float) -> None:
        if self._gapless:
            raise ValueError("Cannot use crossfade when gapless mode is enabled.")

        self._crossfade = value

    @property
    def crossfadeVolume(self) -> Union[float, None]:
        if self._gapless:
            return None

        return 1.0 / (self.client.crossfade / Config.DELAY)

    @property
    def gapless(self) -> bool:
        return self._gapless

    @gapless.setter()
    def gapless(self, value: bool) -> None:
        self._gapless = value

    @property
    def current(self) -> AudioSource:
        if self._current:
            return self._current

        if self.next:
            self._current, self.next = self._next, None

            if not self._current.BufferLoader:
                self.event.dispatch("SOURCE_START", song=self._current)
                self._current.start()

            return self._current

        return None

    @current.setter
    def current(self, value: None) -> None:
        self.event.dispatch("SOURCE_END", song=self._current)

        self.client.loop.call_soon_threadsafe(self._current.cleanup)
        self._current = None

    @property
    def next(self) -> AudioSource:
        if not self._next:
            if not self.client.Queue:
                self.event.dispatch("REQUIRE_NEXT_SOURCE", current=self._current)

                return None

            self._next = self.client.Queue[0]

        if isinstance(self._next, AudioData):

            def setSource(Source: AudioSource) -> None:
                if Source.AudioData == self.client.Queue[0]:
                    self.client.Queue[0] = Source

            self.getSource(self._next, setSource)

            return None

        if self._next != self.client.Queue[0]:
            self._next = None

        if not self._next.BufferLoader:
            if self.current.remain <= (Config.PRELOAD_TIME - (self.crossfade or 0)):
                self.event.dispatch("SOURCE_START", self._next)
                self._next.start()

        return self._next

    @next.setter
    def next(self, value: None) -> None:
        if not self._next:
            return

        if self.client.Queue:
            _nextItem = (
                self._next.AudioData
                if isinstance(self._next, AudioSource)
                else self._next
            )
            _queueItem = (
                self.client.Queue[0].AudioData
                if isinstance(self.client.Queue[0], AudioSource)
                else self.client.Queue[0]
            )

            if _nextItem == _queueItem:
                self.client.Queue.pop()

        self._next = None

    def getSource(self, *args, **kwargs) -> None:
        if self._getSourceTask and not self._getSourceTask.done():
            self._getSourceTask = self.client.loop.create_task(
                self._getSource(*args, **kwargs)
            )

    async def _getSource(self, Data: AudioData, callback: Callable) -> None:
        Source = await Data.source()

        Source.volume = 1.0
        Source.filter = self.client.filter

        callback(Source)

    def read(self) -> bytes:
        if not self.current:
            return

        Data = self.current.read()

        if not Data:
            self._crossfadeLoop = 0
            self.current = None

        if not self._gapless and not (
            self.current.AudioData and self.current.AudioData.is_live
        ):
            if self.current.remain <= self.crossfade:
                NextData = self.next.read()
                if NextData:
                    self._crossfadeLoop += 1
                    crossfadeVolume = self.crossfadeVolume * self._crossfadeLoop

                    self.current.volume = 1.0 - crossfadeVolume
                    self.next.volume = 1.0 + crossfadeVolume

                    Data = audioop.add(Data, NextData, 2)
        else:
            self.next.volume = 1.0
            if self.current.volume != 1.0:
                self.current.volume = round(self.current.volume + 0.01, 3)

        if self.volume != 1.0:
            Data = audioop.mul(Data, 2, min(self.volume, 2.0))

        return Data

    def speak(self, state: bool) -> None:
        if self.client.speakState == state:
            return

        asyncio.run_coroutine_threadsafe(self.client.ws.speak(state), self.client.loop)

    def __do_run(self) -> None:
        self.loops = 0
        _start = time.perf_counter

        while not self._end.is_set():
            try:
                if not self.client._connectedThread.is_set():
                    self.client._connectedThread.wait()
                    self.loops = 0
                    _start = time.perf_counter()

                Data = self.read() if not self.client.paused else None

                if self._volume != self.client.volume:
                    if self._volume < self.client.volume:
                        self._volume = round(self._volume + 0.01, 3)
                    if self._volume > self.client.volume:
                        self._volume = round(self._volume - 0.01, 3)

                self.speak(bool(Data))

                if Data:
                    if self._volume != 1.0:
                        Data = audioop.mul(Data, 2, min(self._volume, 2.0))

                    self.client.send(Data)

                self.loops += 1
                nextTime = _start + self.DELAY * self.loops
                time.sleep(max(0, self.DELAY + (nextTime - time.perf_counter())))
            except:
                self.event.dispatch(
                    "PLAYER_TRACEBACK", traceback=traceback.format_exc()
                )

    def run(self) -> None:
        try:
            self.__do_run()
        except:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        self._end.set()
        self.speak(False)