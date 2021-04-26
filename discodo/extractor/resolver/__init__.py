from typing import Union

import aiohttp

from ...config import Config
from .melon import resolve as melon_resolve
from .spotify import resolve as spotify_resolve
from .vibe import resolve as vibe_resolve


async def resolve(query: str, session=None) -> Union[str, list]:
    if "melon" in Config.ENABLED_EXT_RESOLVER:
        query = await melon_resolve(query, session)
    if "spotify" in Config.ENABLED_EXT_RESOLVER:
        query = await spotify_resolve(query)
    if "vibe" in Config.ENABLED_EXT_RESOLVER:
        query = await vibe_resolve(query, session)

    return query
