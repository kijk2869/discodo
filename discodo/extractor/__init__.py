import asyncio
import ipaddress
import re
import urllib.parse
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


async def extract(
    query: Union[str, list],
    address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = None,
    **kwargs
) -> dict:
    connector = aiohttp.TCPConnector(local_addr=(str(address), 0)) if address else None

    query = await resolve(query, connector)

    if isinstance(query, list):
        Tasks = list(
            map(lambda x: asyncio.Task(extract(x, address=address, **kwargs)), query)
        )

        await asyncio.wait(Tasks)

        Results = []
        for Task in Tasks:
            try:
                Results.append(Task.result())
            except:
                pass

        return Results

    if not URL_REGEX.match(query):
        searchResult: list = await Youtube.search(query, connector)

        if not searchResult:
            raise NoSearchResults

        return searchResult[0]

    Match = YOUTUBE_PLAYLIST_ID_REGEX.match(query)
    if Match:
        if Match.group(1).startswith(("RD", "UL", "PU")):
            urlInfo = urllib.parse.parse_qs(urllib.parse.urlparse(query).query)

            if urlInfo.get("v") and urlInfo.get("list"):
                return await Youtube.extract_mix(
                    urlInfo["v"][0], urlInfo.get("list")[0], connector
                )
        else:
            return await Youtube.extract_playlist(Match.group(1), connector)

    return await youtube_dl_extract(query, address=address, **kwargs)


search = Youtube.search
