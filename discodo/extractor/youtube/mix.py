import json
import re

import aiohttp

DATA_JSON = re.compile(
    r"(?:window\[\"ytInitialData\"\]|var ytInitialData)\s*=\s*(\{.*\})"
)

YOUTUBE_HEADERS = {
    "x-youtube-client-name": "1",
    "x-youtube-client-version": "2.20201030.01.00",
}


async def extract_mix(vId: str, playlistId: str) -> dict:
    if not playlistId.startswith(("RD", "UL", "PU")):
        raise TypeError("playlistId is not Youtube Mix id")

    async with aiohttp.ClientSession(headers=YOUTUBE_HEADERS) as session:
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
            "url": "https://youtube.com/watch?v=" + Renderer["videoId"],
            "uploader": Renderer["longBylineText"]["runs"][0]["text"],
            "duration": sum(
                [
                    int(value) * ((index * 60) if index else 1)
                    for index, value in enumerate(
                        reversed(Renderer["lengthText"]["simpleText"].split(":"))
                    )
                ]
            ),
        }

    return list(map(extract, Playlist["contents"]))