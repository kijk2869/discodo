import asyncio
import contextlib
import ipaddress
import re
import urllib.parse
from typing import Union

import aiohttp

from ..config import Config
from ..errors import NoSearchResults
from .local import extract as local_extract
from .resolver import resolve
from .youtube import Youtube
from .youtube_dl import extract as youtube_dl_extract

URL_REGEX = re.compile(
    r"(?:https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})"
)

YOUTUBE_VIDEO_ID_REGEX = re.compile(
    r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
)

YOUTUBE_PLAYLIST_ID_REGEX = re.compile(
    r"(?:http|https|)(?::\/\/|)(?:www.|)(?:music.|)(?:youtu\.be\/|youtube\.com(?:\/embed\/|\/v\/|\/watch\?v=|\/ytscreeningroom\?v=|\/feeds\/api\/videos\/|\/user\S*[^\w\-\s]|\S*[^\w\-\s]))([\w\-]{12,})[a-z0-9;:@#?&%=+\/\$_.-]*(?:&index=|)([0-9]*)?"
)


async def extract(
    query: Union[str, list],
    address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = None,
    search: bool = False,
    **kwargs,
) -> dict:
    async with aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(local_addr=(str(address), 0))
        if address
        else None
    ) as session:
        query = await resolve(query, session)

        if isinstance(query, list):
            Tasks = list(
                map(
                    lambda x: asyncio.Task(extract(x, address=address, **kwargs)), query
                )
            )

            await asyncio.wait(Tasks)

            Results = []
            for Task in Tasks:
                with contextlib.suppress(Exception):
                    Results.append(Task.result())

            return Results

        if "local" in Config.ENABLED_EXT_RESOLVER:
            localResult = await local_extract(query)

            if localResult:
                return localResult

        if not URL_REGEX.match(query):
            try:
                searchResult: list = await Youtube.search(query, session)
            except:
                pass
            else:
                if not searchResult:
                    raise NoSearchResults

                return searchResult if search else searchResult[0]

        Match = YOUTUBE_PLAYLIST_ID_REGEX.match(query)
        if Match:
            if Match.group(1).startswith(("RD", "UL", "PU")):
                urlInfo = urllib.parse.parse_qs(urllib.parse.urlparse(query).query)

                if urlInfo.get("v") and urlInfo.get("list"):
                    return await Youtube.extract_mix(
                        urlInfo["v"][0], urlInfo.get("list")[0], session
                    )
            else:
                return await Youtube.extract_playlist(Match.group(1), session)

        return await youtube_dl_extract(query, address=address, **kwargs)
