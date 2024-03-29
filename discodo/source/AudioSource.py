import time
from typing import Any, Coroutine, NoReturn

from ..errors import NotSeekable
from .PyAVSource import PyAVSource


class AudioSource(PyAVSource):
    def __init__(self, *args, AudioData=None, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.AudioData = AudioData
        self.address = self.AudioData.address if self.AudioData else None

        self.Context = AudioData.Context
        self._skipped: bool = False

    def toDict(self) -> dict:
        Value = self.AudioData.toDict() if self.AudioData else {}

        Value["_type"] = "AudioSource"
        Value["seekable"] = self.seekable
        Value["duration"] = self.duration
        Value["context"] = self.Context
        Value["as_of"] = time.time()
        if hasattr(self, "position"):
            Value["position"] = self.position

        return Value

    @classmethod
    def fromDict(cls, data):
        raise TypeError("AudioSource cannot be made from dictionary.")

    def __repr__(self) -> str:
        return (
            f"<AudioSource id={self.id} title='{self.title}' duration={self.duration}"
            + (f" position={self.position}" if hasattr(self, "position") else "")
            + f" seekable={self.seekable} address='{self.address}'>"
        )

    def __getattr__(self, key: str) -> Any:
        return getattr(self.AudioData, key)

    @property
    def seekable(self) -> bool:
        return not self.AudioData.is_live if self.AudioData else True

    def seek(self, *args, **kwargs):
        if not self.seekable:
            raise NotSeekable

        return super().seek(*args, **kwargs)

    @property
    def duration(self) -> float:
        return self._duration if self._duration else self.AudioData.duration

    @property
    def remain(self) -> float:
        return round(self.duration - self.position, 2)

    @property
    def filter(self) -> dict:
        return self._filter

    @filter.setter
    def filter(self, value: dict) -> None:
        if self.AudioData and self.AudioData.is_live and "atempo" in value:
            raise ValueError("Cannot use `atempo` filter in live streaming.")

        self._filter = value

    @property
    def skipped(self) -> bool:
        return self._skipped

    @skipped.setter
    def skipped(self, Value: bool) -> None:
        if Value:
            self.stop()

        self._skipped = Value

    def skip(self) -> None:
        self.skipped = True
