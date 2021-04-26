import aiohttp
import pytest

from discodo.extractor.resolver import melon, vibe


@pytest.mark.asyncio
async def testMelon() -> None:
    async with aiohttp.ClientSession() as session:
        assert await melon.get_album(
            "https://www.melon.com/album/detail.htm?albumId=10541761", session
        ) == ["쿠기 (Coogie) - POW (Feat. GRAY)"]


@pytest.mark.asyncio
async def testVibe() -> None:
    async with aiohttp.ClientSession() as session:
        assert await vibe.getChart("total", session)

        assert await vibe.getChart("genre-OS101", session)

        assert await vibe.getTrack("1", session) == "강산에 - 거꾸로 강을 거슬러 오르는 저 힘찬 연어들처럼"

        assert await vibe.getAlbum("1", session) == [
            "강산에 - 거꾸로 강을 거슬러 오르는 저 힘찬 연어들처럼",
            "강산에 - 미스템버린",
            "강산에 - 코메디",
            "강산에 - 억지",
            "강산에 - 내마음의 구멍",
            "강산에 - '98 아리랑",
            "강산에 - 춤추는 나",
            "강산에 - Cat Walk",
            "강산에 - 맛!",
            "강산에 - 나비의 입맞춤",
        ]
