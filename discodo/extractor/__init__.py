import asyncio
import ipaddress
import re
from typing import Union

import aiohttp

from ..errors import NoSearchResults
from .resolver import resolve
from .youtube import Youtube
from .youtube_dl import extract as youtube_dl_extract

URL_REGEX = re.compile(
    r"(?:https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
)

YOUTUBE_PLAYLIST_ID_REGEX = re.compile(
    r"(?:http|https|)(?::\/\/|)(?:www.|)(?:music.|)(?:youtu\.be\/|youtube\.com(?:\/embed\/|\/v\/|\/watch\?v=|\/ytscreeningroom\?v=|\/feeds\/api\/videos\/|\/user\S*[^\w\-\s]|\S*[^\w\-\s]))([\w\-]{12,})[a-z0-9;:@#?&%=+\/\$_.-]*(?:&index=|)([0-9]*)?"
)

YOUTUBE_MIX_PLAYLIST_REGEX = re.compile(
    r"^(?:http|https|)(?::\/\/|)(?:www.|)(?:music.|)youtube\.com\/watch\?(?:&.*)*(?:(?:v=([a-zA-Z0-9_\-]{11})(?:&.*)*&list=([a-zA-Z0-9_\-]{18}))|(?:list=([a-zA-Z0-9_\-]{18})(?:&.*)*&v=([a-zA-Z0-9_\-]{11})))(?:&.*)*(?:\#.*)*$"
)


async def extract(
    query: Union[str, list],
    address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = None,
    **kwargs
) -> dict:
    connector = aiohttp.TCPConnector(local_addr=(str(address), 0)) if address else None

    query = await resolve(query, connector)

    if isinstance(query, list):
        Done, _ = await asyncio.wait(
            [youtube_dl_extract(Item, address=address, **kwargs) for Item in query]
        )

        Results = []
        for Future in Done:
            try:
                Results.append(Future.result())
            except:
                pass

        return Results

    if not URL_REGEX.match(query):
        searchResult: list = await Youtube.search(query, connector)

        if not searchResult:
            raise NoSearchResults

        return searchResult[0]

    Match = YOUTUBE_MIX_PLAYLIST_REGEX.match(query)
    if Match and Match.group(2).startswith(("RD", "UL", "PU")):
        return await Youtube.extract_mix(Match.group(1), Match.group(2), connector)

    Match = YOUTUBE_PLAYLIST_ID_REGEX.match(query)
    if Match and not Match.group(1).startswith(("RD", "UL", "PU")):
        return await Youtube.extract_playlist(Match.group(1), connector)

    return await youtube_dl_extract(query, address=address, **kwargs)


search = Youtube.search