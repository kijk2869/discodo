import asyncio
from typing import Union

from .melon import get_query as melon_get_query
from .spotify import get_query as spotify_get_query
from .youtube_dl import extract as youtube_dl_extract


async def extract(query: Union[str, list], *args, **kwargs) -> dict:
    query = await melon_get_query(query)
    query = await spotify_get_query(query)

    if isinstance(query, list):
        Done, _ = await asyncio.wait(
            [youtube_dl_extract(Item, *args, **kwargs) for Item in query]
        )

        Results = []
        for Future in Done:
            try:
                Results.append(Future.result())
            except:
                pass

        return Results

    return await youtube_dl_extract(query, *args, **kwargs)
