import av


class AudioFifo(av.AudioFifo):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def read(self, samples=20):
        AudioFrame = super().read(samples)
        if not AudioFrame:
            return

        return AudioFrame.planes[0].to_bytes()

    def reset(self):
        self.ptr = None
