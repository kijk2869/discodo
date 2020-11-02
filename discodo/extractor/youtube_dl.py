import asyncio
import copy
import ipaddress
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
    "noplaylist": True,
}


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
