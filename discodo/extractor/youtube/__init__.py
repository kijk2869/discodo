import re

YOUTUBE_HEADERS: dict = {
    "x-youtube-client-name": "1",
    "x-youtube-client-version": "2.20201030.01.00",
}

CONTINUATIONS_CONTEXT: dict = {
    "client": {"clientName": "WEB", "clientVersion": "2.20211019.06.00"}
}

DATA_JSON = re.compile(r'(?:window\["ytInitialData"\]|ytInitialData)\W?=\W?({.*?});')
API_KEY = re.compile(r'INNERTUBE_API_KEY":"(.*?)"')

from .mix import extract_mix
from .playlist import extract_playlist
from .search import search
from .subtitle import get_subtitle


class Youtube:
    extract_mix = extract_mix
    extract_playlist = extract_playlist
    search = search
    get_subtitle = get_subtitle
