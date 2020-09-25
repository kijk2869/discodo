from typing import Union
from .youtube_dl import extract as youtube_dl_extract
from .melon import get_query as melon_get_query
import logging
import asyncio


log = logging.getLogger("discodo.extractor")


async def extract(query: Union[str, list], *args, **kwargs) -> dict:
    query = await melon_get_query(query)

    if isinstance(query, list):
        Done, _ = await asyncio.wait(
            [youtube_dl_extract(Item, *args, **kwargs) for Item in query]
        )

        return [Future.result() for Future in Done]

    return await youtube_dl_extract(query, *args, **kwargs)