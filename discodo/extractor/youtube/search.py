import itertools
import json
import logging

from . import DATA_JSON, YOUTUBE_HEADERS

log = logging.getLogger("discodo.extractor.youtube")


async def search(Query: str, session):
    log.info(f"Downloading search page of {Query}")
    async with session.get(
        "https://www.youtube.com/results",
        headers=YOUTUBE_HEADERS,
        params={"search_query": Query},
    ) as resp:
        Body: str = await resp.text()

    Search = DATA_JSON.search(Body)

    if not Search:
        raise ValueError

    Data = json.loads(Search.group(1))

    def extract_video(Data: dict):
        Renderer = Data.get("videoRenderer")

        if not Renderer or not Renderer.get("lengthText"):
            return

        return {
            "id": Renderer["videoId"],
            "title": Renderer["title"]["runs"][0]["text"],
            "webpage_url": "https://www.youtube.com/watch?v=" + Renderer["videoId"],
            "uploader": Renderer["ownerText"]["runs"][0]["text"],
            "duration": sum(
                [
                    int(value) * (60 ** index)
                    for index, value in enumerate(
                        reversed(Renderer["lengthText"]["simpleText"].split(":"))
                    )
                ]
            ),
        }

    Videos = list(
        filter(
            None,
            map(
                extract_video,
                itertools.chain.from_iterable(
                    map(
                        lambda x: x.get("itemSectionRenderer", {}).get("contents", []),
                        Data["contents"]["twoColumnSearchResultsRenderer"][
                            "primaryContents"
                        ]["sectionListRenderer"]["contents"],
                    )
                ),
            ),
        )
    )

    return Videos
