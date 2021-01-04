import re
from typing import Union

import aiohttp

URL_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?vibe\.naver\.com/(chart|track|album)/?(\d+)?"
)
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko",
    "accept": "application/json",
}

CHART_TYPE = {
    "total": "https://apis.naver.com/vibeWeb/musicapiweb/vibe/v1/chart/track/total",
    "domestic": "https://apis.naver.com/vibeWeb/musicapiweb/vibe/v1/chart/track/domestic",
    "billboardKpop": "https://apis.naver.com/vibeWeb/musicapiweb/vibe/v1/chart/billboard/kpop",
    "oversea": "https://apis.naver.com/vibeWeb/musicapiweb/vibe/v1/chart/track/oversea",
    "billboardTrack": "https://apis.naver.com/vibeWeb/musicapiweb/chart/billboard/track",
    "video": "https://apis.naver.com/vibeWeb/musicapiweb/vibe/v1/chart/video/total",
    "search": "https://apis.naver.com/vibeWeb/musicapiweb/vibe/v1/chart/track/search",
}


async def getChart(type: str, connector: aiohttp.TCPConnector = None) -> list:
    if not type:
        type = "total"

    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        genreMatch = re.match(r"genre-(\w{1,2}\d{3})", type)

        if genreMatch:
            URL = (
                "https://apis.naver.com/vibeWeb/musicapiweb/vibe/v1/chart/track/genres/"
                + genreMatch.group(1)
            )
        else:
            URL = CHART_TYPE.get(type)

            if not URL:
                return

        async with session.get(URL) as resp:
            if resp.status == 404:
                return

            Data = await resp.json()

    return list(
        map(
            lambda x: f"{', '.join(map(lambda y: y['artistName'], x['artists']))} - {x['trackTitle']}",
            Data["response"]["result"]["chart"]["items"]["tracks"],
        )
    )


async def getTrack(id: str, connector: aiohttp.TCPConnector = None) -> list:
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        async with session.get(
            f"https://apis.naver.com/vibeWeb/musicapiweb/track/{id}"
        ) as resp:
            if resp.status == 404:
                return

            Data = await resp.json()

    Track = Data["response"]["result"]["track"]
    return f"{', '.join(map(lambda y: y['artistName'], Track['artists']))} - {Track['trackTitle']}"


async def getAlbum(id: str, connector: aiohttp.TCPConnector = None) -> list:
    async with aiohttp.ClientSession(headers=headers, connector=connector) as session:
        async with session.get(
            f"https://apis.naver.com/vibeWeb/musicapiweb/album/{id}/tracks"
        ) as resp:
            if resp.status == 404:
                return

            Data = await resp.json()

    return list(
        map(
            lambda x: f"{', '.join(map(lambda y: y['artistName'], x['artists']))} - {x['trackTitle']}",
            Data["response"]["result"]["tracks"],
        )
    )


async def resolve(
    query: str, connector: aiohttp.TCPConnector = None
) -> Union[str, list]:
    Match = URL_REGEX.match(query)

    if Match:
        if Match.group(1) == "chart":
            query = await getChart(Match.group(2), connector) or query
        elif Match.group(1) == "track":
            query = await getTrack(Match.group(2), connector) or query
        elif Match.group(2) == "album":
            query = await getAlbum(Match.group(2), connector) or query

    return query
