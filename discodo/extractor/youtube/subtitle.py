import logging
import urllib.parse

try:
    from defusedxml import cElementTree as ElementTree
except ImportError:
    from defusedxml import ElementTree

import aiohttp

log = logging.getLogger("discodo.extractor.youtube")


async def get_subtitle(videoId: str, connector: aiohttp.TCPConnector = None) -> list:
    log.info(f"Downloading subtitle page of {videoId}")
    async with aiohttp.ClientSession(connector=connector) as session:
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
