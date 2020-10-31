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


async def extract_playlist(playlistId: str) -> dict:
    if playlistId.startswith(("RD", "UL", "PU")):
        raise TypeError("playlistId is Youtube Mix id")

    async with aiohttp.ClientSession(headers=YOUTUBE_HEADERS) as session:
        async with session.get(
            f"https://www.youtube.com/playlist", params={"list": playlistId, "hl": "en"}
        ) as resp:
            Body: str = await resp.text()

        Search = DATA_JSON.search(Body)

        if not Search:
            raise ValueError

        Data: dict = json.loads(Search.group(1))

        if Data.get("alerts"):
            raise Exception(Data["alerts"][0]["alertRenderer"]["text"]["simpleText"])

        firstPlaylistData: list = Data["contents"]["twoColumnBrowseResultsRenderer"][
            "tabs"
        ][0]["tabRenderer"]["content"]["sectionListRenderer"]["contents"][0][
            "itemSectionRenderer"
        ][
            "contents"
        ][
            0
        ][
            "playlistVideoListRenderer"
        ]

        Sources: list = []

        def extract_playlist(playlistData: dict) -> str:
            trackList: list = playlistData.get("contents")
            if not trackList:
                return

            def extract(Track: dict) -> dict:
                Renderer: dict = Track.get("playlistVideoRenderer")
                shortBylineText: dict = Renderer.get("shortBylineText")

                if not Renderer.get("isPlayable") or not shortBylineText:
                    return

                return {
                    "id": Renderer["videoId"],
                    "title": Renderer["title"].get("simpleText")
                    or Renderer["title"]["runs"][0]["text"],
                    "url": "https://youtube.com/watch?v=" + Renderer["videoId"],
                    "uploader": shortBylineText["runs"][0]["text"],
                    "duration": Renderer["lengthSeconds"],
                }

            Sources.extend(list(map(extract, trackList)))

            if not playlistData.get("continuations"):
                return

            continuationsToken: str = playlistData["continuations"][0][
                "nextContinuationData"
            ]["continuation"]
            return (
                "https://www.youtube.com/browse_ajax?continuation="
                + continuationsToken
                + "&ctoken="
                + continuationsToken
                + "&hl=en"
            )

        continuations_url: str = extract_playlist(firstPlaylistData)
        while True:
            if not continuations_url:
                break

            async with session.get(continuations_url) as resp:
                Body: dict = await resp.json()

            nextPlaylistData: dict = Body[1]["response"]["continuationContents"][
                "playlistVideoListContinuation"
            ]

            continuations_url: str = extract_playlist(nextPlaylistData)

        return Sources


import asyncio

print(asyncio.run(extract_playlist("PLBPpXidFYT4b6sPA5T4mKeZkWQzSOWGi7"), debug=True))
