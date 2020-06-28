from ..extractor import extract
from .AudioSource import AudioSource


class AudioData:
    def __init__(self, data):
        self.id = data.get('id')
        self.title = data.get('title')

        if data.get('_type') == 'url' and data.get('ie_key') == 'Youtube':
            self.webpage_url = f'https://www.youtube.com/watch?v={self.id}'
            self.thumbnail = f'https://i.ytimg.com/vi/{self.id}/hqdefault.jpg'
        else:
            self.webpage_url = data.get('webpage_url')
            self.thumbnail = data.get('thumbnail')

        self.duration = data.get('duration')
        self.stream_url = data.get('url')
        self.is_live = data.get('is_live', False)

        self.uploader = data.get('uploader')
        self.description = data.get('description')
        self.subtitles = data.get('subtitles')

        self.playlist = data.get('playlist')

        self._source = None

    @classmethod
    async def create(cls, query):
        Data = await extract(query)

        if isinstance(Data, list):
            return [cls(Item) for Item in Data]

        return cls(Data)

    async def gather(self):
        Data = await extract(self.webpage_url)
        self.__init__(Data)

        return self

    async def source(self, *args, **kwargs):
        if not self.stream_url:
            await self.gather()

        if not self._source:
            self._source = AudioSource(
                self.stream_url, *args, AudioData=self, **kwargs)

        return self._source

    def toDict(self):
        return {
            'id': self.id,
            'title': self.title,
            'webpage_url': self.webpage_url,
            'thumbnail': self.thumbnail,
            'duration': self.duration,
            'is_live': self.is_live,
            'uploader': self.uploader,
            'description': self.description,
            'playlist': self.playlist
        }
