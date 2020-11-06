import json
import logging

import aiohttp

from ...config import Config
from . import DATA_JSON, YOUTUBE_HEADERS

log = logging.getLogger("discodo.extractor.youtube")


async def extract_playlist(
    playlistId: str, connector: aiohttp.TCPConnector = None
) -> dict:
    if playlistId.startswith(("RD", "UL", "PU")):
        raise TypeError("playlistId is Youtube Mix id")

    log.info(f"Downloading playlist page of {playlistId}")
    async with aiohttp.ClientSession(
        headers=YOUTUBE_HEADERS, connector=connector
    ) as session:
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

        def extract_playlist(playlistData: dict, name: str = "contents") -> str:
            trackList: list = playlistData.get(name)
            if not trackList:
                return

            continuationsTokens: list = []

            def extract(Track: dict) -> dict:
                if "playlistVideoRenderer" in Track:
                    Renderer: dict = Track.get("playlistVideoRenderer", {})
                    shortBylineText: dict = Renderer.get("shortBylineText")

                    if not Renderer.get("isPlayable") or not shortBylineText:
                        return

                    return {
                        "id": Renderer["videoId"],
                        "title": Renderer["title"].get("simpleText")
                        or Renderer["title"]["runs"][0]["text"],
                        "webpage_url": "https://youtube.com/watch?v="
                        + Renderer["videoId"],
                        "uploader": shortBylineText["runs"][0]["text"],
                        "duration": Renderer["lengthSeconds"],
                    }
                elif "continuationItemRenderer" in Track:
                    continuationsTokens.append(
                        Track["continuationItemRenderer"]["continuationEndpoint"][
                            "continuationCommand"
                        ]["token"]
                    )

                    return
                else:
                    return

            Sources.extend(map(extract, trackList))

            if not continuationsTokens:
                return

            return (
                "https://www.youtube.com/browse_ajax?continuation="
                + continuationsTokens[0]
                + "&ctoken="
                + continuationsTokens[0]
                + "&hl=en"
            )

        continuations_url: str = extract_playlist(firstPlaylistData)
        for _ in range(Config.PLAYLIST_PAGE_LIMIT):
            if not continuations_url:
                break

            log.info(f"Downloading playlist continuation page of {playlistId}")
            async with session.get(continuations_url) as resp:
                Body: dict = await resp.json()

            nextPlaylistData: dict = Body[1]["response"]["onResponseReceivedActions"][
                0
            ]["appendContinuationItemsAction"]

            continuations_url: str = extract_playlist(
                nextPlaylistData, name="continuationItems"
            )

        return list(filter(None, Sources))
