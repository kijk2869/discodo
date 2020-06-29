import logging
import asyncio
from re import compile as Regex
from youtube_dl import YoutubeDL as YoutubeDLClient

log = logging.getLogger("discodo.extractor")

YOUTUBE_PLAYLIST_ID_REGEX = Regex(
    r'(?:http|https|)(?::\/\/|)(?:www.|)(?:music.|)(?:youtu\.be\/|youtube\.com(?:\/embed\/|\/v\/|\/watch\?v=|\/ytscreeningroom\?v=|\/feeds\/api\/videos\/|\/user\S*[^\w\-\s]|\S*[^\w\-\s]))([\w\-]{12,})[a-z0-9;:@#?&%=+\/\$_.-]*(?:&index=|)([0-9]*)?')


def _extract(query):
    option = {
        'format': '(bestaudio[ext=opus]/bestaudio/best)[protocol!=http_dash_segments]',
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0',
        'logger': log,
        'skip_download': True,
        'writesubtitles': True
    }

    YoutubePlaylistMatch = YOUTUBE_PLAYLIST_ID_REGEX.match(query)
    if YoutubePlaylistMatch:
        if YoutubePlaylistMatch.group(1).startswith(('RD', 'UL', 'PU')):
            option['playlist_items'] = '25'  # handle Youtube Mix Playlist

        option['playliststart'] = int(YoutubePlaylistMatch.group(
            2)) if YoutubePlaylistMatch.group(2).isdigit() else 1
        option['dump_single_json'] = True
        option['extract_flat'] = True
    else:
        option['noplaylist'] = True

    YoutubeDL = YoutubeDLClient(option)
    Data = YoutubeDL.extract_info(query, download=False)

    # if 'entries' in Data:
    #     Items = []
    #     for Item in Data['entries']:
    #         Item['playlist'] = {
    #             'id': Data['id'],
    #             'title': Data['title'],
    #             'url': Data['webpage_url'],
    #             'uploader': Data['uploader'],
    #             'uploader_id': Data['uploader_id'],
    #             'uploader_url': Data['uploader_url']
    #         }
    #         Items.append(Item)

    #     return Items
    if 'entries' in Data:
        return Data['entries']

    return Data


async def extract(query, loop=None):
    if not loop:
        loop = asyncio.get_event_loop()

    return await loop.run_in_executor(None, _extract, query)
