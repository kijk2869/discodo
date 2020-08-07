import asyncio
import logging
from re import compile as Regex
from typing import Optional
from urllib.error import HTTPError

from youtube_dl import YoutubeDL as YoutubeDLClient

from .exceptions import NoSearchResults

log = logging.getLogger("discodo.extractor")

YOUTUBE_PLAYLIST_ID_REGEX = Regex(
    r"(?:http|https|)(?::\/\/|)(?:www.|)(?:music.|)(?:youtu\.be\/|youtube\.com(?:\/embed\/|\/v\/|\/watch\?v=|\/ytscreeningroom\?v=|\/feeds\/api\/videos\/|\/user\S*[^\w\-\s]|\S*[^\w\-\s]))([\w\-]{12,})[a-z0-9;:@#?&%=+\/\$_.-]*(?:&index=|)([0-9]*)?"
)


def _extract(query: str, planner=None) -> Optional[dict]:
    option = {
        "format": "(bestaudio[ext=opus]/bestaudio/best)[protocol!=http_dash_segments]",
        "nocheckcertificate": True,
        "ignoreerrors": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",
        "logger": log,
        "skip_download": True,
        "writesubtitles": True,
    }

    IPAddress = planner.get() if planner else None
    if IPAddress:
        option["source_address"] = IPAddress.__str__()

    YoutubePlaylistMatch = YOUTUBE_PLAYLIST_ID_REGEX.match(query)
    if YoutubePlaylistMatch and not YoutubePlaylistMatch.group(1).startswith(
        ("RD", "UL", "PU")
    ):
        option["playliststart"] = (
            int(YoutubePlaylistMatch.group(2))
            if YoutubePlaylistMatch.group(2).isdigit()
            else 1
        )
        option["dump_single_json"] = True
        option["extract_flat"] = True
        query = "https://www.youtube.com/playlist?list=" + YoutubePlaylistMatch.group(1)
    else:
        option["noplaylist"] = True

    YoutubeDL = YoutubeDLClient(option)
    try:
        Data = YoutubeDL.extract_info(query, download=False)
    except HTTPError as e:
        if e.cause.code == 429:
            IPAddress.givePenalty()

        raise e

    if not Data:
        raise NoSearchResults

    if "entries" in Data:
        if len(Data["entries"]) == 1:
            return Data["entries"][0]

        return Data["entries"]

    return Data


def _clear_cache():
    option = {"ignoreerrors": True, "no_warnings": True, "logger": log}

    YoutubeDL = YoutubeDLClient(option)
    YoutubeDL.cache.remove()


async def extract(query, planner=None, loop=None):
    if not loop:
        loop = asyncio.get_event_loop()

    return await loop.run_in_executor(None, _extract, query, planner)


async def clear_cache(loop=None):
    if not loop:
        loop = asyncio.get_event_loop()

    return await loop.run_in_executor(None, _clear_cache)
