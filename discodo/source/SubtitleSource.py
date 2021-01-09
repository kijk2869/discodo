import re

try:
    from defusedxml import cElementTree as ElementTree
except ImportError:
    from defusedxml import ElementTree

import aiohttp
from markdownify import markdownify

from .abc import SubtitleFormat


class smi(SubtitleFormat):
    BODY_REGEX = re.compile(r"<body>([\w|\W|\s]+)</body>", flags=re.I)
    SYNC_REGEX = re.compile(r"<Sync Start=([0-9]+)>([\s|\w|\W]+)", flags=re.I)

    def __init__(self, Body: str) -> None:
        super().__init__()

        self._TextElements = []

        for Text in [
            Item.strip()
            for Item in self.BODY_REGEX.search(Body).group(1).splitlines()
            if Item.strip()
        ]:
            if Text.lower().startswith("<sync"):
                Match = self.SYNC_REGEX.match(Text)

                Start, Element = round(int(Match.group(1)) / 1000, 2), Match.group(2)

                if self._TextElements:
                    self._TextElements[-1]["end"] = Start - 1
                    self._TextElements[-1]["duration"] = (
                        self._TextElements[-1]["end"] - self._TextElements[-1]["start"]
                    )

                self._TextElements.append({"start": Start, "text": Element})
            elif self._TextElements:
                self._TextElements[-1]["text"] += "\n" + Text

        self.TextElements = {
            TextElement["start"]: dict(
                TextElement,
                markdown=markdownify(TextElement["text"]).strip(),
                end=TextElement.get("end") or TextElement["start"] + 5,
                duration=TextElement.get("duration") or 5,
            )
            for TextElement in self._TextElements
            if markdownify(TextElement["text"]).strip()
        }

        self.duration = sorted(
            [TextElement["end"] for TextElement in self.TextElements.values()]
        )[-1]

    @classmethod
    async def load(cls, URL: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as session:
                Data = await session.text()

        # Blocking is suspicious
        return cls(Data)


class srv1(SubtitleFormat):
    def __init__(self, Data: str):
        super().__init__()

        self.Tree = ElementTree.fromstring(Data)

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
                "markdown": markdownify(TextElement.text),
            }
            for TextElement in self.Tree.findall("text")
            if "dur" in TextElement.attrib
        }

        self.duration = sorted(
            [TextElement["end"] for TextElement in self.TextElements.values()]
        )[-1]

    @classmethod
    async def load(cls, URL: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(URL) as session:
                Data = await session.text()

        return cls(Data)
