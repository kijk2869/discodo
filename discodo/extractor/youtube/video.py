import collections
import json
import logging
import re
import time
import urllib.parse
from itertools import chain
from typing import Generator, Union

import aiohttp

log = logging.getLogger("discodo.extractor.youtube")

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

SIGNATURE_FUNCTION_REGEXS = list(
    map(
        re.compile,
        [
            r"\b[cs]\s*&&\s*[adf]\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(",
            r"\b[a-zA-Z0-9]+\s*&&\s*[a-zA-Z0-9]+\.set\([^,]+\s*,\s*encodeURIComponent\s*\(\s*(?P<sig>[a-zA-Z0-9$]+)\(",
            r'(?:\b|[^a-zA-Z0-9$])(?P<sig>[a-zA-Z0-9$]{2})\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)',
            r'(?P<sig>[a-zA-Z0-9$]+)\s*=\s*function\(\s*a\s*\)\s*{\s*a\s*=\s*a\.split\(\s*""\s*\)',
        ],
    )
)

EXTRACT_JAVASCRIPT_FUNCTION_REGEX = lambda funcname: (
    r"(?x)"
    + r"(?:function\s+{funcname}|[".format(funcname=funcname)
    + r"{;,]\s"
    + r"*{funcname}\s*=\s*function|var\s+{funcname}\s*=\s*function)\s*".format(
        funcname=funcname
    )
    + r"\((?P<args>[^)]*)\)\s*"
    + r"\{(?P<code>[^}]+)\}"
)

FUNCTION_CALL_REGEX = re.compile(
    r"(?P<var>[a-zA-Z0-9]+)\.(?P<key>[a-zA-Z0-9]+)\(\w\s*,\s*(?P<value>[0-9]+)\)"
)

FUNCTION_TRANSFORM_REGEX = re.compile(r"var Zu={(.*?)};", flags=re.DOTALL)


def swap(Array: list, b: int) -> list:
    r = b % len(Array)
    return list(chain([Array[r]], Array[1:r], [Array[0]], Array[r + 1 :]))


FUNCTION_TO_PYTHON_MAP: dict = {
    re.compile(r".reverse"): lambda Array, *_: Array[::-1],
    re.compile(r".splice\((?P<start>.*?),(?P<end>.*?)\)"): lambda Array, end: Array[
        :end
    ]
    + Array[end * 2 :],
    re.compile(
        r"{var\s\w=\w\[0\];\w\[0\]=\w\[\w\%\w.length\];\w\[\w\%\w(?:\.length)*\]=\w}"
    ): swap,
}

AUDIO_QUALITY_PRIORITY: dict = {
    "AUDIO_QUALITY_LOW": 1,
    "AUDIO_QUALITY_MEDIUM": 2,
    "AUDIO_QUALITY_HIGH": 3,
}


async def checkPlayabilityStatus(Data: dict) -> str:
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
        log.info(f"Downloading polymer page of {videoId}")
        async with session.get(
            "https://www.youtube.com/watch",
            params={"v": videoId, "hl": "en", "pbj": "1"},
        ) as resp:
            Data: dict = await resp.json()
        InitialData: dict = Data[2]

        Status: str = await checkPlayabilityStatus(InitialData)
        playerResponse: dict = InitialData["playerResponse"]

        embedConfig: dict = {}

        async def extract_embed_config() -> None:
            log.info(f"Age restricted, downloading embed page of {videoId}")
            async with session.get("https://www.youtube.com/embed/" + videoId) as resp:
                Body: str = await resp.text()

            Search = EMBED_CONFIG_REGEX.findall(Body)

            if not Search:
                raise ValueError("Could not extract embed player config.")

            for config in Search:
                embedConfig.update(json.loads(config.replace("'", '"')))

        if Status == "LOGIN_REQUIRED":
            await extract_embed_config()

            embedPlayerResponse: dict = json.loads(
                InitialData.get("player_response")
                or embedConfig["PLAYER_CONFIG"]
                .get("args", {})
                .get("embedded_player_response")
            )

            log.info(f"Downloading video info of {videoId}")
            async with session.get(
                "https://www.youtube.com/get_video_info",
                params={
                    "video_id": videoId,
                    "eurl": "https://youtube.googleapis.com/v/" + videoId,
                    "sts": embedPlayerResponse.get("sts", ""),
                    "hl": "en_GB",
                },
            ) as resp:
                videoInfoBody: str = await resp.text()

            videoInfo: dict = urllib.parse.parse_qs(videoInfoBody)
            if videoInfo.get("player_response"):
                playerResponse: dict = json.loads(
                    videoInfo.get("player_response", [None])[0]
                )

        videoDetails: dict = playerResponse["videoDetails"]

        def formatGenerator() -> Generator:
            streamingData: dict = playerResponse.get("streamingData", {})

            for formatData in streamingData.get("formats", []):
                yield formatData
            for formatData in streamingData.get("adaptiveFormats", []):
                yield formatData

        formats: list = []
        for formatData in formatGenerator():
            if formatData.get("drmFamilies") or formatData.get("drm_families"):
                return

            if formatData.get("type") == "FORMAT_STREAM_TYPE_OTF":
                return

            url: str = formatData.get("url")
            if url:
                urlData: dict = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
            else:
                urlData: dict = urllib.parse.parse_qs(formatData["signatureCipher"])
                url: str = urlData.get("url", [None])[0]

            formatId: int = formatData.get("itag") or urlData["itag", [None]][0]
            if not formatId:
                continue

            formatId: str = str(formatId)

            if videoDetails.get("useCipher", False):
                if not url:
                    continue

                if "sig" in urlData:
                    url += "&signature=" + urlData["sig"][0]
                elif "s" in urlData:
                    if not embedConfig:
                        await extract_embed_config()

                    encryptedSignature: str = urlData["s"][0]
                    playerScriptUrl: str = urllib.parse.urljoin(
                        "https://www.youtube.com/",
                        embedConfig["WEB_PLAYER_CONTEXT_CONFIGS"][
                            "WEB_PLAYER_CONTEXT_CONFIG_ID_EMBEDDED_PLAYER"
                        ]["jsUrl"],
                    )

                    log.info(f"Downloading player script of {videoId}")
                    async with session.get(playerScriptUrl) as resp:
                        Code: str = await resp.text()

                    Search = None
                    for regex in SIGNATURE_FUNCTION_REGEXS:
                        Search = regex.search(Code)

                        if Search:
                            break

                    if not Search:
                        raise ValueError(
                            "Could not extract signiture decrypt function name."
                        )

                    funcMatch = re.search(
                        EXTRACT_JAVASCRIPT_FUNCTION_REGEX(
                            re.escape(Search.group("sig"))
                        ),
                        Code,
                    )

                    FuncCodes: list = funcMatch.group("code").split(";")
                    Transforms: dict = collections.defaultdict(dict)

                    Signature: str = ""
                    DummySignature: list = []

                    for FuncCode in FuncCodes:
                        log.debug(f"Parsing javascript code: {FuncCode}")

                        if FuncCode == 'a=a.split("")':
                            DummySignature: list = list(encryptedSignature)
                        elif FuncCode == 'return a.join("")':
                            Signature: str = "".join(DummySignature)
                        else:
                            Match = FUNCTION_CALL_REGEX.search(FuncCode)

                            if not Match:
                                raise ValueError("could not parse function")

                            if not Match.group("var") in Transforms:
                                Search = FUNCTION_TRANSFORM_REGEX.search(Code)

                                if not Search:
                                    raise ValueError(
                                        "Could not extract function transform."
                                    )

                                TransformValues: list = (
                                    Search.group(1).replace("\n", " ").split(", ")
                                )

                                for TransformValue in TransformValues:
                                    name, function = TransformValue.split(":", 1)
                                    for regex, func in FUNCTION_TO_PYTHON_MAP.items():
                                        if regex.search(function):
                                            Transforms[Match.group("var")][name] = func

                            DummySignature: list = Transforms[Match.group("var")][
                                Match.group("key")
                            ](DummySignature, int(Match.group("value")))

                    url += "&" + urlData.get("sp", ["sig"])[0] + "=" + Signature

            if "ratebypass" not in url:
                url += "&ratebypass=yes"

            formats.append(
                {
                    "itag": formatId,
                    "mimeType": formatData.get("mimeType"),
                    "audioQuality": formatData.get("audioQuality"),
                    "url": url,
                    "expires_in": time.time()
                    + int(
                        playerResponse.get("streamingData", {}).get("expiresInSeconds")
                    ),
                }
            )

    formatHaveAudio: list = list(
        filter(lambda format: bool(format["audioQuality"]), formats)
    )

    sortedWithPriority: list = sorted(
        formatHaveAudio,
        key=lambda format: AUDIO_QUALITY_PRIORITY.get(format["audioQuality"], 0),
        reverse=True,
    )