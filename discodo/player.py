import asyncio
import audioop
import threading
from typing import Union
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
        if self._current:
            self.client.loop.call_soon_threadsafe(self._current.cleanup)
        if self._next:
            self.client.loop.call_soon_threadsafe(self._next.cleanup)

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
            self._current, self._next = self._next, None

            if not self._current.BufferLoader:
                # Event: Song Start
                self._current.start()

            return self._current

        return None

    @current.setter
    def current(self, value: None) -> None:
        # Event: Song End

        self.client.loop.call_soon_threadsafe(self._current.cleanup)
        self._current = None

    @property
    def next(self) -> AudioSource:
        if not self._next:
            if self.client._Queue.empty():
                # Event: Need Song

                return None

            self._next = self.client._Queue.get_nowait()

        if isinstance(self._next, AudioData):
            self.getSource(self, "_next", self._next)

            return None

        if not self._next.BufferLoader:
            if self.current.remain <= (Config.PRELOAD_TIME - (self.crossfade or 0)):
                # Event: Song Start
                self._next.start()

        return self._next

    def getSource(self, *args, **kwargs) -> None:
        if self._getSourceTask and not self._getSourceTask.done():
            self._getSourceTask = self.client.loop.create_task(
                self._getSource(*args, **kwargs)
            )

    async def _getSource(self, object, attribute: str, Data: AudioData) -> None:
        Source = await Data.source()

        Source.volume = 1.0
        # TODO: set filter

        setattr(object, attribute, Source)

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
                traceback.print_exc()

    def run(self):
        try:
            self._do_run()
        except:
            pass
        finally:
            self.stop()

    def stop(self) -> None:
        self._end.set()
        self.speak(False)