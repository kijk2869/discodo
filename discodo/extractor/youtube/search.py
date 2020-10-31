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


async def search(Query: str) -> None:
    async with aiohttp.ClientSession(headers=YOUTUBE_HEADERS) as session:
        async with session.get(
            "https://www.youtube.com/results", params={"search_query": Query}
        ) as resp:
            Body: str = await resp.text()

    Search = DATA_JSON.search(Body)

    if not Search:
        raise ValueError

    Data = json.loads(Search.group(1))

    def extract_video(Data: dict) -> dict:
        Renderer: dict = Data.get("videoRenderer")

        if not Renderer or not Renderer.get("lengthText"):
            return

        return {
            "id": Renderer["videoId"],
            "title": Renderer["title"]["runs"][0]["text"],
            "url": "https://www.youtube.com/watch?v=" + Renderer["videoId"],
            "uploader": Renderer["ownerText"]["runs"][0]["text"],
            "duration": sum(
                [
                    int(value) * ((index * 60) if index else 1)
                    for index, value in enumerate(
                        reversed(Renderer["lengthText"]["simpleText"].split(":"))
                    )
                ]
            ),
        }

    Videos: list = list(
        filter(
            None,
            map(
                extract_video,
                Data["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"][
                    "sectionListRenderer"
                ]["contents"][0]["itemSectionRenderer"]["contents"],
            ),
        )
    )

    return Videos