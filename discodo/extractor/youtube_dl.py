import asyncio
import copy
import ipaddress
import re
from typing import Coroutine, Union

from youtube_dl import YoutubeDL as YoutubeDLClient

from ..errors import NoSearchResults

YTDLOption = {
    "format": "(bestaudio[ext=opus]/bestaudio/best)[protocol!=http_dash_segments]",
    "nocheckcertificate": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "skip_download": True,
    "writesubtitles": True,
}

YOUTUBE_PLAYLIST_ID_REGEX = re.compile(
    r"(?:http|https|)(?::\/\/|)(?:www.|)(?:music.|)(?:youtu\.be\/|youtube\.com(?:\/embed\/|\/v\/|\/watch\?v=|\/ytscreeningroom\?v=|\/feeds\/api\/videos\/|\/user\S*[^\w\-\s]|\S*[^\w\-\s]))([\w\-]{12,})[a-z0-9;:@#?&%=+\/\$_.-]*(?:&index=|)([0-9]*)?"
)


def _extract(
    query: str,
    address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = None,
    video: bool = False,
) -> dict:
    option = copy.copy(YTDLOption)

    if video:
        option["format"] = "(best)[protocol!=http_dash_segments]"

    if address:
        option["source_address"] = str(address)

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
    Data = YoutubeDL.extract_info(query, download=False)

    if not Data:
        raise NoSearchResults

    if "entries" in Data:
        if len(Data["entries"]) == 1:
            return Data["entries"][0]

        return Data["entries"]

    if not Data:
        raise NoSearchResults

    return Data


def _clear_cache() -> None:
    option = {
        "ignoreerrors": True,
        "no_warnings": True,
    }

    YoutubeDL = YoutubeDLClient(option)
    YoutubeDL.cache.remove()


def extract(
    query: str,
    address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = None,
    video: bool = False,
    loop: asyncio.AbstractEventLoop = None,
) -> Coroutine:
    if not loop:
        loop = asyncio.get_event_loop()

    return loop.run_in_executor(None, _extract, query, address, video)


def clear_cache(loop: asyncio.AbstractEventLoop = None) -> Coroutine:
    if not loop:
        loop = asyncio.get_event_loop()

    return loop.run_in_executor(None, _clear_cache)
