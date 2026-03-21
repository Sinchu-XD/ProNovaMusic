import time
import aiohttp
from .Core import db


_session = None


async def get_session():
    global _session
    if _session is None:
        timeout = aiohttp.ClientTimeout(total=5)
        _session = aiohttp.ClientSession(timeout=timeout)
    return _session


async def is_stream_valid(url):
    try:
        session = await get_session()
        async with session.head(url, allow_redirects=True) as resp:
            return resp.status == 200
    except:
        return False


async def get_stream_cache(key):
    try:
        data = await db.yt_stream_cache.find_one({"_id": key})
        if not data:
            return None

        stream = data.get("stream")
        if not stream:
            return None

        if await is_stream_valid(stream):
            return stream

        return None
    except:
        return None


async def set_stream_cache(key, stream):
    try:
        await db.yt_stream_cache.update_one(
            {"_id": key},
            {
                "$set": {
                    "stream": stream,
                    "time": time.time()
                }
            },
            upsert=True
        )
    except:
        pass
