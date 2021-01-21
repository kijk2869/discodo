import asyncio
import audioop
import threading
import time
import traceback
from typing import Callable, Union

from .config import Config
from .errors import NotPlaying
from .source import AudioData, AudioSource


class Player(threading.Thread):
    def __init__(self, client) -> None:
        threading.Thread.__init__(self)
        self.daemon = True

        self.client = client

        self._volume = 1.0
        self._crossfade = 5.0
        self._end = threading.Event()

        self._getSourceTask = None
        self._current = self._next = None

        self.loops = 0
        self._crossfadeLoop = 0
        self._request_dispatched = False

    def __del__(self) -> None:
        for Source in self.client.Queue:
            if isinstance(Source, AudioSource):
                Source.cleanup()

    @property
    def crossfade(self) -> Union[float, None]:
        return self._crossfade

    @crossfade.setter
    def crossfade(self, value: float) -> None:
        self._crossfade = value

    @property
    def crossfadeVolume(self) -> Union[float, None]:
        return (
            (1.0 / (self.client.crossfade / Config.DELAY))
            if self.client.crossfade
            else 1.0
        )

    def seek(self, offset: int) -> None:
        if not self.current:
            raise NotPlaying

        return self.current.seek(offset)

    @property
    def current(self) -> AudioSource:
        if not self._current:
            if self.next:
                self._current, self.next = self.next, None
            else:
                return None

        if self._current.filter != self.client.filter:
            self._current.filter = self.client.filter

        if not self._current.BufferLoader:
            self.client.dispatcher.dispatch("SOURCE_START", source=self._current)
            self._current.start()

        return self._current

    @current.setter
    def current(self, _: None) -> None:
        self.client.dispatcher.dispatch("SOURCE_END", source=self._current)

        self.client.loop.call_soon_threadsafe(self._current.cleanup)
        self._current = None

    @property
    def next(self) -> AudioSource:
        is_load_condition = (
            not self._current
            or self._current.skipped
            or (
                self._current.remain <= (Config.PRELOAD_TIME + self.crossfade)
                and not (self._current.AudioData and self._current.AudioData.is_live)
            )
        )

        if not self._next:
            if not self.client.Queue:
                if self._current and is_load_condition and not self._request_dispatched:
                    self.client.dispatcher.dispatch(
                        "REQUIRE_NEXT_SOURCE",
                        current=self._current,
                        autoplay=self.client.autoplay,
                    )
                    self._request_dispatched = True

                return None

            self._next = self.client.Queue[0]
            self._request_dispatched = False

        if not self.client.Queue or self._next != self.client.Queue[0]:
            self._next = None
            return None

        if isinstance(self._next, AudioData):
            if is_load_condition:

                def setSource(Source: Union[AudioData, AudioSource]) -> None:
                    if isinstance(Source, AudioData) and Source == self.client.Queue[0]:
                        self._next = None
                        self.client.Queue.pop(0)
                    if (
                        isinstance(Source, AudioSource)
                        and Source.AudioData == self.client.Queue[0]
                    ):
                        self._next = self.client.Queue[0] = Source

                self.getSource(self._next, setSource)
            return None

        if self._next.filter != self.client.filter:
            self._next.filter = self.client.filter

        if self._current and not self._next.BufferLoader:
            if is_load_condition:
                self.client.dispatcher.dispatch("SOURCE_START", source=self._next)
                self._next.start()

        return self._next

    @next.setter
    def next(self, _: None) -> None:
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
                self.client.Queue.pop(0)
        self._next = None

    def getSource(self, *args, **kwargs) -> None:
        if not self._getSourceTask or self._getSourceTask.done():
            self._getSourceTask = asyncio.run_coroutine_threadsafe(
                self._getSource(*args, **kwargs), self.client.loop
            )

    async def _getSource(self, Data: AudioData, callback: Callable) -> None:
        try:
            Source = await Data.source()

            Source.volume = 1.0
            Source.filter = self.client.filter
        except Exception:
            traceback.print_exc()
            self.client.dispatcher.dispatch(
                "SOURCE_TRACEBACK", source=Data, traceback=traceback.format_exc()
            )

            Source = Data
        finally:
            callback(Source)

    def read(self) -> bytes:
        if not self.current:
            return

        Data = self.current.read()

        if not Data or self.current.volume <= 0.0:
            self._crossfadeLoop = 0
            self.current = None

            return self.read()

        is_crossfade_timing = self.next and (
            (
                self.current.remain <= self.crossfade
                and not (self.current.AudioData and self.current.AudioData.is_live)
            )
            or self.current.skipped
        )

        if is_crossfade_timing and self.next.AudioFifo.is_ready():
            NextData = self.next.read()
            if NextData:
                self._crossfadeLoop += 1
                crossfadeVolume = self.crossfadeVolume * self._crossfadeLoop

                self.current.volume = 1.0 - crossfadeVolume
                self.next.volume = crossfadeVolume

                Data = audioop.add(Data, NextData, 2)
        elif self.next:
            self.next.volume = 1.0 if self.crossfade == 0 else 0.0

        if not self.next and self.current.skipped and not self.client.Queue:
            if self.current.volume > 0.0:
                self.current.volume = round(self.current.volume - 0.01, 3)
        elif not is_crossfade_timing:
            if self.current.volume < 1.0:
                self.current.volume = round(self.current.volume + 0.01, 3)
            elif self.current.volume > 1.0:
                self.current.volume = 1.0

        return Data

    def speak(self, state: bool) -> None:
        if self.client.speakState == state:
            return

        self.client.speakState = state
        asyncio.run_coroutine_threadsafe(self.client.ws.speak(state), self.client.loop)

    def __do_run(self) -> None:
        self.loops = 0
        _start = time.perf_counter()

        while not self._end.is_set():
            try:
                if not self.client.connectedThreadEvent.is_set():
                    self.client.connectedThreadEvent.wait()
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
                nextTime = _start + Config.DELAY * self.loops
                time.sleep(max(0, Config.DELAY + (nextTime - time.perf_counter())))
            except Exception:
                traceback.print_exc()
                self.dispatcher.dispatch(
                    "PLAYER_TRACEBACK", traceback=traceback.format_exc()
                )

    def run(self) -> None:
        try:
            self.__do_run()
        except Exception:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        self._end.set()
        self.speak(False)
