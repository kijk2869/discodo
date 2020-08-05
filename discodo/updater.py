import asyncio
import os
import re
import sys
from logging import getLogger

import aiohttp

from . import __version__

log = getLogger("discodo.updater")

loop = asyncio.get_event_loop()
VERSION_FETCH = re.compile(
    r"<h1 class=\"package-header__name\">\s*(discodo (a-Z|0-9|.+))\n\s*<\/h1>",
    flags=re.S,
)


async def get_version():
    log.debug("fetching latest version from pypi.")
    async with aiohttp.ClientSession() as session:
        async with session.get("https://pypi.org/project/discodo/") as response:
            Data = await response.text()

    Match = VERSION_FETCH.search(Data)
    return Match.group(2)


async def check_version():
    version = await get_version()

    if not version.startswith(__version__):
        print(
            "\n" * 5
            + f"Package update is required! | Now {__version__}, Latest {version}"
            + "\n" * 5
        )

        try:
            os.system(f"{sys.executable} -m pip install --upgrade discodo")
        except Exception as e:
            print(f"Auto updating failed, {e.__name__}: {e}")
    else:
        log.info(f"package is now up to date | Now {__version__}")
