from xml.etree import ElementTree

from aiohttp import ClientSession
from markdownify import markdownify


class srv1:
    def __init__(self, Tree):
        self.Tree = Tree

        self.TextElements = {
            float(TextElement.attrib["start"]): {
                "start": float(TextElement.attrib["start"]),
                "duration": float(TextElement.attrib["dur"]),
                "end": round(
                    float(TextElement.attrib["start"])
                    + float(TextElement.attrib["dur"]),
                    2,
                ),
                "text": TextElement.text,
                "markdown": markdownify(TextElement.text).strip(),
            }
            for TextElement in self.Tree.findall("text")
        }

        self.duration = sorted(
            [TextElement["end"] for TextElement in self.TextElements.values()]
        )[-1]

        self.time = 0.0
        self.current = None

    @classmethod
    async def load(cls, URL: str):
        async with ClientSession() as session:
            async with session.get(URL) as session:
                Data = await session.text()

        Tree = ElementTree.fromstring(Data)
        return cls(Tree)

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

    @property
    def json(self) -> dict:
        return self.TextElements

    @property
    def lyrics(self) -> str:
        if self.current:
            return self.current
        return None

    @property
    def is_done(self) -> bool:
        return self.time >= self.duration
