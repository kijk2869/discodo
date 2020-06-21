import av


class AudioFifo(av.AudioFifo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read(self, samples=20):
        return self.read(samples)

    def reset(self):
        self.ptr = None
