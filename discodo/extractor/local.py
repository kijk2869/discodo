import asyncio
import os

import av


def _extract(query: str):
    if not (
        os.path.exists(query) and os.path.isfile(query) and os.access(query, os.R_OK)
    ):
        return

    try:
        container = av.open(query)

        if not container.streams.audio:
            return

        filename = os.path.split(query)[1]
        duration = round(container.duration / 1000000, 2)
    except av.InvalidDataError:
        return
    finally:
        container.close()

    return {
        "id": os.path.splitext(filename)[0],
        "title": filename,
        "url": query,
        "duration": duration,
        "is_file": True,
    }


def extract(
    query: str,
    loop: asyncio.AbstractEventLoop = None,
):
    if not loop:
        loop = asyncio.get_event_loop()

    return loop.run_in_executor(None, _extract, query)
