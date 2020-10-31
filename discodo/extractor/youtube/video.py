import json
import re
import urllib.parse
from typing import Union

import aiohttp

YOUTUBE_VIDEO_REGEX = re.compile(
    r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
)

YOUTUBE_VIDEO_NOTAVAILABLE_REGEX = list(
    map(
        re.compile,
        [
            r'(?s)<h1[^>]+id=["\']unavailable-message["\'][^>]*>(.+?)</h1>',
            r'(?s)<div[^>]+id=["\']unavailable-submessage["\'][^>]*>(.+?)</div>',
        ],
    )
)

YOUTUBE_PLAYER_CONFIG_REGEX = re.compile(
    r";ytplayer\.config\s*=\s*({.+?});(?:ytplayer)?"
)

YOUTUBE_REDIRECT_REGEX = re.compile(r"[\?&]next_url=([^&]+)")

YOUTUBE_AGE_RESTRICTED_REGEXS = list(
    map(
        re.compile,
        [
            r"og:restrictions:age",
            r'player-age-gate-content">',
        ],
    )
)

YOUTUBE_EMBED_STS_REGEX = re.compile(r'"sts"\s*:\s*(\d+)')


def json_or_none(Body: str) -> Union[dict, None]:
    if not Body:
        return

    return json.loads(Body)


async def extract(url: str) -> dict:
    _redirect = YOUTUBE_REDIRECT_REGEX.search(url)
    if _redirect:
        url: str = "https://www.youtube.com/" + urllib.parse.unquote(
            _redirect.group(1)
        ).lstrip("/")

    videoId: str = YOUTUBE_VIDEO_REGEX.match(url).group(5)

    video_info: dict = {}
    player_response: dict = {}

    is_live: bool = None
    view_count: int = None

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://www.youtube.com/watch?v={videoId}",
            params={"gl": "US", "hl": "en", "has_verified": "1", "bpctr": "9999999999"},
        ) as resp:
            Body: str = await resp.text()
            videoId: str = resp.url.query.get("v", videoId)

        if any([regex.search(Body) for regex in YOUTUBE_AGE_RESTRICTED_REGEXS]):
            async with session.get(f"https://www.youtube.com/embed/{videoId}") as resp:
                EmbedBody: str = await resp.text()

            sts_match = YOUTUBE_EMBED_STS_REGEX.search(EmbedBody)
            sts: str = sts_match.group(1) if sts_match else ""

            async with session.get(
                "https://www.youtube.com/get_video_info",
                params={
                    "video_id": videoId,
                    "eurl": f"https://youtube.googleapis.com/v/{videoId}",
                    "sts": sts,
                },
            ) as resp:
                InfoBody: str = await resp.text()

            video_info: dict = urllib.parse.parse_qs(InfoBody)

            player_response: dict = json_or_none(video_info.get("player_response"))
        else:
            player_config_match = YOUTUBE_PLAYER_CONFIG_REGEX.search(Body)

            if player_config_match:
                player_config: dict = json.loads(player_config_match.group(1))

                video_info: dict = player_config["args"]

                is_live: bool = (
                    video_info.get("livestream") == "1"
                    or video_info.get("live_playback") == 1
                )
                player_response: dict = json_or_none(video_info.get("player_response"))

        if not (video_info or player_response):
            message = "\n".join(
                [
                    match.group(1)
                    for match in filter(
                        map(
                            lambda regex: regex.search(Body),
                            YOUTUBE_VIDEO_NOTAVAILABLE_REGEX,
                        )
                    )
                    if match
                ]
            )

            raise ValueError(f"Unable to extract video: {message}")

        if not isinstance(video_info, dict):
            video_info: dict = {}

        video_details: dict = player_response.get("videoDetails", {})
        microformat: dict = player_response.get("microformat", {}).get(
            "playerMicroformatRenderer", {}
        )

        Title: str = video_info.get("title") or video_details.get("title")

        if view_count is None and video_info.get("view_count", []):
            view_count: int = video_info["view_count"][0]
        if view_count is None:
            for Data in [video_details, microformat]:
                if not Data:
                    continue

                if video_details.get("viewCount", "").isdigit():
                    view_count: int = int(video_details["viewCount"])
                    break

        if is_live is None:
            is_live = bool(video_details.get("isLive", False))

        if "ypc_video_rental_bar_text" in video_info and "author" not in video_info:
            raise ValueError("this is rental video")

        streaming_formats: list = player_response.get("streamingData", {}).get(
            "formats", []
        )
        streaming_formats += player_response.get("streamingData", {}).get(
            "adaptiveFormats", []
        )

        if "conn" in video_info and video_info["conn"][0].startswith("rtmp"):
            formats: list = [{"protocol": "rtmp", "url": video_info["conn"][0]}]
        elif not is_live and (
            streaming_formats
            or len(video_info.get("url_encoded_fmt_stream_map", "")) >= 1
            or len(video_info.get("adaptive_fmts", "")) >= 1
        ):
            encoded_url_map: str = (
                video_info.get("url_encoded_fmt_stream_map", "")
                + ","
                + video_info.get("adaptive_fmts", "")
            )

            if "rtmpe%3Dyes" in encoded_url_map:
                raise ValueError("rtmpe using encrypt")


import asyncio

print(asyncio.run(extract("https://www.youtube.com/watch?v=TnWPeBgN0q0")))
