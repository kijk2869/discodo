import json
import re
from typing import Union
import urllib.parse

import aiohttp

YOUTUBE_HEADERS = {
    "x-youtube-client-name": "1",
    "x-youtube-client-version": "2.20201030.01.00",
}

YOUTUBE_REDIRECT_REGEX = re.compile(r"[\?&]next_url=([^&]+)")

YOUTUBE_VIDEO_REGEX = re.compile(
    r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
)

EMBED_CONFIG_REGEX = re.compile(
    r"yt\.setConfig\((.*?)\);(?=yt\.setConfig|writeEmbed\(\);)"
)


def checkPlayabilityStatus(Data: dict) -> str:
    playabilityStatus: dict = Data["playerResponse"].get("playabilityStatus", {})
    Status: Union[str, None] = playabilityStatus.get("status")

    if not Status:
        raise ValueError("There is no playability status.")
    elif Status == "OK":
        return "OK"
    elif Status == "ERROR":
        reason: str = playabilityStatus["reason"]

        raise ValueError(reason)
    elif Status == "UNPLAYABLE":
        Renderer: dict = playabilityStatus["errorScreen"]["playerErrorMessageRenderer"]
        reason: str = playabilityStatus["reason"]

        if Renderer.get("subreason"):
            if Renderer["subreason"].get("simpleText"):
                reason: str = Renderer["subreason"]["simpleText"]
            elif isinstance(Renderer["subreason"].get("runs"), list):
                reason: str = "\n".join(
                    map(lambda Data: Data["text"], Renderer["subreason"]["runs"])
                )

        raise ValueError(reason)
    elif Status == "LOGIN_REQUIRED":
        reason: str = playabilityStatus["errorScreen"]["playerErrorMessageRenderer"][
            "reason"
        ]["simpleText"]

        if reason == "Private video":
            raise ValueError("This is a private video.")

        return "LOGIN_REQUIRED"
    else:
        raise ValueError(f"Not handled playability status. {Status}")


async def extract(url: str) -> dict:
    _redirect = YOUTUBE_REDIRECT_REGEX.search(url)
    if _redirect:
        url: str = "https://www.youtube.com/" + urllib.parse.unquote(
            _redirect.group(1)
        ).lstrip("/")

    videoId: str = YOUTUBE_VIDEO_REGEX.match(url).group(5)

    async with aiohttp.ClientSession(headers=YOUTUBE_HEADERS) as session:
        async with session.get(
            "https://www.youtube.com/watch",
            params={"v": videoId, "hl": "en", "pbj": "1"},
        ) as resp:
            Data: dict = await resp.json()
        InitialData: dict = Data[2]

        Status: str = checkPlayabilityStatus(InitialData)
        playerResponse: dict = InitialData["playerResponse"]

        print(playerResponse.keys())

        if Status == "LOGIN_REQUIRED":
            async with session.get("https://www.youtube.com/embed/" + videoId) as resp:
                Body: str = await resp.text()

            Search = EMBED_CONFIG_REGEX.findall(Body)

            if not Search:
                raise ValueError("Could not extract embed player config.")

            embedConfig: dict = {}
            for config in Search:
                embedConfig.update(json.loads(config.replace("'", '"')))

            playerResponse: dict = json.loads(
                InitialData.get("player_response")
                or embedConfig["PLAYER_CONFIG"]
                .get("args", {})
                .get("embedded_player_response")
            )

        return playerResponse.keys()


import asyncio

