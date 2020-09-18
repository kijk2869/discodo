from typing import Coroutine

from ..errors import NotSeekable
from .PyAVSource import PyAVSource


class AudioSource(PyAVSource):
    def __init__(self, *args, AudioData=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.AudioData = AudioData

    def __dict__(self) -> dict:
        Value = dict(self.AudioData) if self.AudioData else None

        Value["_type"] = "AudioSource"
        Value["seekable"] = self.seekable
        Value["duration"] = self.duration
        Value["position"] = self.position

        return Value

    @property
    def seekable(self) -> bool:
        return not self.AudioData.is_live if self.AudioData else True

    def seek(self, *args, **kwargs) -> Coroutine:
        if not self.seekable:
            raise NotSeekable

        return super().seek(*args, **kwargs)

    @property
    def duration(self) -> float:
        return super().duration if super().duration else self.AudioData.duration

    @property
    def remain(self) -> float:
        return round(self.duration - self.position, 2)

    @property
    def filter(self) -> dict:
        return super().filter

    @filter.setter
    def filter(self, value: dict) -> dict:
        if self.AudioData and self.AudioData.is_live and "atempo" in value:
            raise ValueError("Cannot use `atempo` filter in live streaming.")

        super().filter = value
