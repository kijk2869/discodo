import abc


class SubtitleFormat(abc.ABC):
    def __init__(self) -> None:
        self.time = 0.0
        self.current = None

    def seek(self, time: float) -> str:
        self.time = float(time)

        if (
            not self.current
            or not self.current["start"] <= self.time < self.current["end"]
        ):
            Elements = [
                TextElement
                for Start, TextElement in self.TextElements.items()
                if Start <= self.time < TextElement["end"]
            ]
            self.current = Elements[-1] if Elements else None

        return self.lyrics

    def __dict__(self) -> dict:
        return self.TextElements

    @property
    def lyrics(self) -> str:
        if self.current:
            return self.current
        return None

    @property
    def is_done(self) -> bool:
        return self.time >= self.duration

    @classmethod
    @abc.abstractmethod
    async def load(cls, URL: str):
        raise NotImplementedError
