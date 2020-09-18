import aiohttp

from ..errors import Forbidden, TooManyRequests
from ..extractor import clear_cache, extract
from .AudioSource import AudioSource


class AudioData:
    def __init__(self, data: dict) -> None:
        self.id, self.title = data["id"], data.get("title")

        if data.get("_type") == "url" and data.get("ie_key") == "Youtube":
            self.webpage_url = f"https://www.youtube.com/watch?v={self.id}"
            self.thumbnail = f"https://i.ytimg.com/vi/{self.id}/hqdefault.jpg"
            self.stream_url = None
        else:
            self.webpage_url = data["webpage_url"]
            self.thumbnail = data["thumbnail"]
            self.stream_url = data["url"]

        self.duration = data.get("duration")
        self.is_live = data.get("is_live", False)

        self.uploader = data.get("uploader")
        self.description = data.get("description")

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
        }

    @classmethod
    async def create(cls, query: str):
        Data = await extract(query)

        if isinstance(Data, list):
            return [cls(Item) for Item in Data]

        return cls(Data)

    async def gather(self):
        Data = await extract(self.webpage_url)
        self.__init__(Data)

        return self

    async def source(
        self, *args, _retry: int = 0, _limited: bool = False, **kwargs
    ) -> AudioSource:
        if not self.stream_url or _limited:
            await self.gather()

        if not self._source:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.stream_url) as resp:
                    Status = resp.status

            if Status == 403:
                if _retry == 0:
                    return await self.source(*args, _retry=_retry + 1, **kwargs)
                elif _retry == 1:
                    await clear_cache()
                    return await self.source(*args, _retry=_retry + 1, **kwargs)

                raise Forbidden
            if Status == 429:
                raise TooManyRequests

            self._source = AudioSource(self.stream_url, *args, AudioData=self, **kwargs)

        return self._source
