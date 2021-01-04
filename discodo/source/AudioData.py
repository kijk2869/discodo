from typing import Any, Dict, List

import aiohttp
import yarl
import youtube_dl

from ..config import Config
from ..errors import Forbidden, TooManyRequests
from ..extractor import extract
from ..extractor.youtube_dl import clear_cache
from .AudioSource import AudioSource


class AudioData:
    def __init__(self, data: dict) -> None:
        self.id = data["id"]
        self.title = data.get("title")

        if data.get("_type") == "url" and data.get("ie_key") == "Youtube":
            self.webpage_url = f"https://www.youtube.com/watch?v={self.id}"
            self.thumbnail = f"https://i.ytimg.com/vi/{self.id}/hqdefault.jpg"
            self.stream_url = None
        else:
            self.webpage_url = data.get("webpage_url")
            self.thumbnail = data.get("thumbnail")
            self.stream_url = data.get("url")

        self.duration = data.get("duration")
        self.is_live = data.get("is_live", False)

        self.uploader = data.get("uploader")
        self.description = data.get("description")

        def getUsableSubtitle(Data: Dict[str, Any]) -> Dict[str, Any]:
            Usable: List[Any] = list(
                filter(lambda Subtitle: Subtitle.get("ext") == "srv1", Data)
            )

            if Usable:
                return Usable[0]["url"]

        self.subtitles = (
            dict(
                map(
                    lambda Data: (
                        Data[0],
                        getUsableSubtitle(Data[1]),
                    ),
                    data["subtitles"].items(),
                )
            )
            if "subtitles" in data
            else {}
        )

        self.chapters = data.get("chapters", {})

        self.related: bool = False

        self._source = None

    def __dict__(self) -> dict:
        return {
            "_type": "AudioData",
            "id": self.id,
            "title": self.title,
            "webpage_url": self.webpage_url,
            "thumbnail": self.thumbnail,
            "url": self.stream_url,
            "duration": self.duration,
            "is_live": self.is_live,
            "uploader": self.uploader,
            "description": self.description,
            "subtitles": self.subtitles,
            "chapters": self.chapters,
            "related": self.related,
        }

    def __repr__(self) -> str:
        return f"<AudioData id={self.id} title='{self.title}' duration={self.duration} address='{self.address}'>"

    @classmethod
    async def create(cls, query: str):
        cls.address = Config.RoutePlanner.get() if Config.RoutePlanner else None

        try:
            Data = await extract(query, address=cls.address)
        except youtube_dl.utils.DownloadError as exc:
            if Config.RoutePlanner and exc.exc_info[1].status == 429:
                Config.RoutePlanner.mark_failed_address(cls.address)

                return await cls.create(query)

            raise exc

        if isinstance(Data, list):
            return [cls(Item) for Item in Data]

        return cls(Data)

    async def gather(self):
        try:
            Data = await extract(self.webpage_url, address=self.address)
        except youtube_dl.utils.DownloadError as exc:
            if Config.RoutePlanner and exc.exc_info[1].status == 429:
                Config.RoutePlanner.mark_failed_address(self.address)
                self.address = Config.RoutePlanner.get()

                return await self.gather()

            raise exc

        self.__init__(Data)

        return self

    async def source(
        self, *args, _retry: int = 0, _limited: bool = False, **kwargs
    ) -> AudioSource:
        if not self.stream_url or _limited:
            await self.gather()

        if not self._source:
            async with aiohttp.ClientSession() as session:
                URL = yarl.URL(self.stream_url, encoded=True)
                async with session.get(URL) as resp:
                    Status = resp.status

            if Status == 403:
                if _retry == 0:
                    return await self.source(
                        *args, _retry=_retry + 1, _limited=True, **kwargs
                    )
                elif _retry == 1:
                    await clear_cache()
                    return await self.source(
                        *args, _retry=_retry + 1, _limited=True, **kwargs
                    )

                raise Forbidden
            if Status == 429:
                if Config.RoutePlanner:
                    Config.RoutePlanner.mark_failed_address(self.address)
                    self.address = Config.RoutePlanner.get()

                    return await self.source(*args, _limited=True, **kwargs)

                raise TooManyRequests

            self._source = AudioSource(self.stream_url, AudioData=self, **kwargs)

        return self._source
