import re
from typing import Union

from asyncspotify import Client, ClientCredentialsFlow

from ...config import Config

URL_REGEX = re.compile(
    r"(?:http(?:s):\/\/open\.spotify\.com\/|spotify:)(playlist|track|album)(?:\/|:)([a-z|A-Z|0-9]+)"
)

spotify = None


async def create_client():
    global spotify

    if spotify:
        return

    import warnings

    warnings.warn(
        "Sporty features are experimental, do not use on production.", UserWarning
    )

    auth = ClientCredentialsFlow(
        client_id=Config.SPOTIFY_ID,
        client_secret=Config.SPOTIFY_SECRET,
    )

    spotify = Client(auth)

    await spotify.authorize()


async def get_track(id: str) -> str:
    Track = await spotify.get_track(id)

    return f"{Track.artists.pop().name} - {Track.name}"


async def get_album(id: str) -> list:
    Tracks = await spotify.get_album_tracks(id)

    return [f"{Track.artists.pop().name} - {Track.name}" for Track in Tracks]


async def get_playlist(id: str) -> list:
    Tracks = await spotify.get_playlist_tracks(id)

    return [f"{Track.artists.pop().name} - {Track.name}" for Track in Tracks]


async def resolve(query: str) -> Union[str, list]:
    if not Config.SPOTIFY_ID or not Config.SPOTIFY_SECRET:
        return query

    if not spotify:
        await create_client()

    URL_PARSE = URL_REGEX.search(query)
    if URL_PARSE:
        if URL_PARSE.group(1) == "track":
            return await get_track(URL_PARSE.group(2))
        elif URL_PARSE.group(1) == "album":
            return await get_album(URL_PARSE.group(2))
        elif URL_PARSE.group(1) == "playlist":
            return await get_playlist(URL_PARSE.group(2))

    return query
