import os
import time
import audioop
import asyncio
import threading

FRAME_LENGTH = os.getenv('FRAME_LENGTH', 20)
DELAY = FRAME_LENGTH / 1000.0


class Player(threading.Thread):
    def __init__(self, voice_client, volume=1.0, loop=None):
        threading.Thread.__init__(self)
        self.daemon = True
        self._end = threading.Event()
        self.loop = loop or asyncio.get_event_loop()

        self.client = voice_client
        self.sources = []

        self._volume = volume

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value):
        self._volume = max(value, 0.0)

    @property
    def current(self):
        return self.sources[0] if self.sources else None

    def add(self, AudioSource):
        self.sources.append(AudioSource)

        return self.sources.index(AudioSource)

    def makeFrame(self):
        if not self.current:
            return

        Data = self.current.read()

        if not Data:
            self.loop.call_soon_threadsafe(self.current.cleanup)
            del self.sources[0]

        return Data

    def _do_run(self):
        self.loops = 0
        _start = time.perf_counter()
        send = self.client.send

        self.speak(True)
        while not self._end.is_set():
            Data = self.makeFrame()

            if Data:
                if self.volume != 1.0:
                    Data = audioop.mul(Data, 2, min(self._volume, 2.0))

                self.loops += 1
                send(Data)

                nextTime = _start + DELAY * self.loops
                time.sleep(max(0, DELAY + (nextTime - time.perf_counter())))

    def run(self):
        try:
            self._do_run()
        finally:
            self.stop()

    def stop(self):
        self._end.set()
        self.speak(False)

    def speak(self, value):
        asyncio.run_coroutine_threadsafe(
            self.client.ws.speak(value), self.client.loop)
