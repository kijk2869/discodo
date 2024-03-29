import json
import logging

from ...config import Config
from . import API_KEY, CONTINUATIONS_CONTEXT, DATA_JSON, YOUTUBE_HEADERS

log = logging.getLogger("discodo.extractor.youtube")


async def extract_playlist(playlistId: str, session):
    if playlistId.startswith(("RD", "UL", "PU")):
        raise TypeError("playlistId is Youtube Mix id")

    log.info(f"Downloading playlist page of {playlistId}")
    async with session.get(
        "https://www.youtube.com/playlist",
        headers=YOUTUBE_HEADERS,
        params={"list": playlistId, "hl": "en"},
    ) as resp:
        Body = await resp.text()

    Search = DATA_JSON.search(Body)

    if not Search:
        raise ValueError

    Data: dict = json.loads(Search.group(1))

    if Data.get("alerts"):
        if Data["alerts"][0]["alertWithButtonRenderer"]["type"] == "ERROR":
            raise Exception(
                Data["alerts"][0]["alertWithButtonRenderer"]["text"]["simpleText"]
            )

    firstPlaylistData = Data["contents"]["twoColumnBrowseResultsRenderer"]["tabs"][0][
        "tabRenderer"
    ]["content"]["sectionListRenderer"]["contents"][0]["itemSectionRenderer"][
        "contents"
    ][
        0
    ][
        "playlistVideoListRenderer"
    ]

    Sources: list = []

    def extract_playlist(playlistData: dict, name: str = "contents"):
        trackList = playlistData.get(name)
        if not trackList:
            return

        continuationsTokens: list = []

        def extract(Track: dict):
            if "playlistVideoRenderer" in Track:
                Renderer: dict = Track.get("playlistVideoRenderer", {})
                shortBylineText = Renderer.get("shortBylineText")

                if not Renderer.get("isPlayable") or not shortBylineText:
                    return

                return {
                    "id": Renderer["videoId"],
                    "title": Renderer["title"].get("simpleText")
                    or Renderer["title"]["runs"][0]["text"],
                    "webpage_url": "https://youtube.com/watch?v=" + Renderer["videoId"],
                    "uploader": shortBylineText["runs"][0]["text"],
                    "duration": Renderer["lengthSeconds"],
                }
            if "continuationItemRenderer" in Track:
                continuationsTokens.append(
                    Track["continuationItemRenderer"]["continuationEndpoint"][
                        "continuationCommand"
                    ]["token"]
                )

                return
            return

        Sources.extend(map(extract, trackList))

        if not continuationsTokens:
            return

        return continuationsTokens[0]

    key = API_KEY.search(Body)

    if not key:
        raise ValueError

    continuations_url = "https://www.youtube.com/youtubei/v1/browse?key=" + key.group(1)

    continuations_key = extract_playlist(firstPlaylistData)
    for _ in range(Config.PLAYLIST_PAGE_LIMIT):
        if not continuations_key:
            break

        log.info(f"Downloading playlist continuation page of {playlistId}")

        continuations_data = {
            "context": CONTINUATIONS_CONTEXT,
            "continuation": continuations_key,
        }

        async with session.post(
            continuations_url, json=continuations_data, headers=YOUTUBE_HEADERS
        ) as resp:
            Body = await resp.json()

        nextPlaylistData = Body["onResponseReceivedActions"][0][
            "appendContinuationItemsAction"
        ]

        continuations_key = extract_playlist(nextPlaylistData, name="continuationItems")

    return list(filter(None, Sources))
