import json
import re

import aiohttp

DATA_JSON = re.compile(
    r"(?:window\[\"ytInitialData\"\]|var ytInitialData)\s*=\s*(\{.*\})"
)


async def search(Query: str) -> None:
    async with aiohttp.ClientSession() as session:
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


if __name__ == "__main__":
    # testing code

    import asyncio

    print(asyncio.run(search("")))