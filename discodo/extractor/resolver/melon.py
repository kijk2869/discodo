import re
from typing import Union

from bs4 import BeautifulSoup

MELON_REGEX = re.compile(
    r"(?:https?:\/\/)?(?:www\.)?melon.com/album/detail.htm\?albumId=([0-9]+)"
)


async def get_album(url: str, session) -> list:
    async with session.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko"
        },
    ) as resp:
        Body = await resp.text()

    soup = BeautifulSoup(Body, "html.parser")

    Table = soup.find("form", attrs={"id": "frm"}).find("table")

    Items = [
        Element.find_all("div", class_="ellipsis")
        for Element in [
            Item.find("div", class_="wrap_song_info") for Item in Table.find_all("tr")
        ]
        if Element
    ]

    return [
        f'{Item[1].find("a").text} - {Item[0].find("a").text} "topic"' for Item in Items if Item
    ]


async def resolve(query: str, session):
    is_album = MELON_REGEX.match(query)

    if is_album:
        Album = await get_album(query, session)

        if len(Album) == 1:
            return Album[0]

        return Album

    return query
