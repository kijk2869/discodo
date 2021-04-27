import re
from typing import Union

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


async def getChart(type: str, session):
    if not type:
        type = "total"

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

    async with session.get(URL, headers=headers) as resp:
        if resp.status == 404:
            return

        Data = await resp.json()

    return list(
        map(
            lambda x: f'{", ".join(map(lambda y: y["artistName"], x["artists"]))} - {x["trackTitle"]} "topic"',
            Data["response"]["result"]["chart"]["items"]["tracks"],
        )
    )


async def getTrack(id: str, session):
    async with session.get(
        f"https://apis.naver.com/vibeWeb/musicapiweb/track/{id}", headers=headers
    ) as resp:
        if resp.status == 404:
            return

        Data = await resp.json()

    Track = Data["response"]["result"]["track"]
    return f'{", ".join(map(lambda y: y["artistName"], Track["artists"]))} - {Track["trackTitle"]} "topic"'


async def getAlbum(id: str, session):
    async with session.get(
        f"https://apis.naver.com/vibeWeb/musicapiweb/album/{id}/tracks", headers=headers
    ) as resp:
        if resp.status == 404:
            return

        Data = await resp.json()

    return list(
        map(
            lambda x: f'{", ".join(map(lambda y: y["artistName"], x["artists"]))} - {x["trackTitle"]} "topic"',
            Data["response"]["result"]["tracks"],
        )
    )


async def resolve(query: str, session):
    Match = URL_REGEX.match(query)

    if Match:
        if Match.group(1) == "chart":
            query = await getChart(Match.group(2), session) or query
        elif Match.group(1) == "track":
            query = await getTrack(Match.group(2), session) or query
        elif Match.group(2) == "album":
            query = await getAlbum(Match.group(2), session) or query

    return query
