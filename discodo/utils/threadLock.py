import threading


class withLock:
    def __init__(self, Lock: threading.Lock):
        self.Lock = Lock

    def __enter__(self):
        self.Lock.acquire()
        return self

    def __exit__(self, type, value, traceback):
        self.Lock.release()
