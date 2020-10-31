import urllib.parse
from xml.etree import ElementTree

import aiohttp


async def get_subtitle(videoId: str) -> list:
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://video.google.com/timedtext",
            params={"hl": "en", "type": "list", "v": videoId},
        ) as resp:
            Body: str = await resp.text()

    Tree = ElementTree.fromstring(Body)

    Subtitles: dict = {}

    for Track in Tree.findall("track"):
        if Track.attrib["lang_code"] in Subtitles:
            continue

        Params = urllib.parse.urlencode(
            {
                "lang": Track.attrib["lang_code"],
                "v": videoId,
                "fmt": "srv1",
                "name": Track.attrib["name"].encode("utf-8"),
            }
        )

        Subtitles[Track.attrib["lang_code"]] = {
            "url": "https://www.youtube.com/api/timedtext?" + Params,
            "ext": "srv1",
        }

    return Subtitles