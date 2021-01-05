import pytest

from discodo.extractor import youtube


@pytest.mark.asyncio
async def testSearch() -> None:
    assert await youtube.search("T7Myg0nHGzg") == [
        {
            "id": "T7Myg0nHGzg",
            "title": "CS:GO CLUCH CLIP (2vs1)",
            "webpage_url": "https://www.youtube.com/watch?v=T7Myg0nHGzg",
            "uploader": "라고솔로가말했습니다",
            "duration": 19,
        }
    ]


@pytest.mark.asyncio
async def testPlaylist() -> None:
    assert await youtube.extract_playlist("PLB6rrfCPynfApD_C0yItgW5WLC0f-wDvG") == [
        {
            "id": "T7Myg0nHGzg",
            "title": "CS:GO CLUCH CLIP (2vs1)",
            "webpage_url": "https://youtube.com/watch?v=T7Myg0nHGzg",
            "uploader": "라고솔로가말했습니다",
            "duration": "19",
        }
    ]
