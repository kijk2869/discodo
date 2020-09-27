import asyncio
import ipaddress
from typing import Union

import aiohttp

from ..config import Config
from .melon import get_query as melon_get_query
from .spotify import get_query as spotify_get_query
from .youtube_dl import extract as youtube_dl_extract


async def extract(
    query: Union[str, list],
    address: Union[ipaddress.IPv4Address, ipaddress.IPv6Address] = None,
    **kwargs
) -> dict:
    connector = aiohttp.TCPConnector(local_addr=(str(address), 0)) if address else None

    if "melon" in Config.ENABLED_EXT_EXTRACTOR:
        query = await melon_get_query(query, connector)
    if "spotify" in Config.ENABLED_EXT_EXTRACTOR:
        query = await spotify_get_query(query)

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

    return await youtube_dl_extract(query, address=address, **kwargs)
