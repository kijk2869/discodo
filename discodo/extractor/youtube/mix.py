import json
import logging

import aiohttp

from . import DATA_JSON, YOUTUBE_HEADERS

log = logging.getLogger("discodo.extractor.youtube")


async def extract_mix(
    vId: str, playlistId: str, connector: aiohttp.TCPConnector = None
) -> dict:
    if not playlistId.startswith(("RD", "UL", "PU")):
        raise TypeError("playlistId is not Youtube Mix id")

    log.info(f"Downloading playlist page of {playlistId}")
    async with aiohttp.ClientSession(
        headers=YOUTUBE_HEADERS, connector=connector
    ) as session:
        async with session.get(
            f"https://www.youtube.com/watch", params={"v": vId, "list": playlistId}
        ) as resp:
            Body: str = await resp.text()

    Search = DATA_JSON.search(Body)

    if not Search:
        raise ValueError

    Data: dict = json.loads(Search.group(1))
    Playlist: dict = Data["contents"]["twoColumnWatchNextResults"]["playlist"][
        "playlist"
    ]

    def extract(Track: dict) -> dict:
        Renderer: dict = Track["playlistPanelVideoRenderer"]

        return {
            "id": Renderer["videoId"],
            "title": Renderer["title"]["simpleText"],
            "webpage_url": "https://youtube.com/watch?v=" + Renderer["videoId"],
            "uploader": Renderer["longBylineText"]["runs"][0]["text"],
            "duration": sum(
                [
                    int(value) * (60 ** index)
                    for index, value in enumerate(
                        reversed(Renderer["lengthText"]["simpleText"].split(":"))
                    )
                ]
            ),
        }

    return list(map(extract, Playlist["contents"]))
