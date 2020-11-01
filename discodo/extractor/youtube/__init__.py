import re

YOUTUBE_HEADERS: dict = {
    "x-youtube-client-name": "1",
    "x-youtube-client-version": "2.20201030.01.00",
}

DATA_JSON = re.compile(
    r"(?:window\[\"ytInitialData\"\]|var ytInitialData)\s*=\s*(\{.*\})"
)

from .mix import extract_mix
from .playlist import extract_playlist
from .search import search
from .subtitle import get_subtitle