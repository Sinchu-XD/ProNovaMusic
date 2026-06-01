import re
import os
import asyncio
import inspect
import time
from traceback import format_exc

from YouTubeMusic.Search import Search
from YouTubeMusic.Stream import get_stream, get_video_stream
from YouTubeMusic.Playlist import get_playlist_songs

from Pronova.Utils.Logger import LOGGER
from Config import COOKIES_PATH


PLAYLIST_REGEX = re.compile(r"(list=)")
YOUTUBE_REGEX = re.compile(r"(youtube\.com|youtu\.be|music\.youtube\.com)")

STREAM_CACHE = {}
CACHE_TTL = 3600


def yt_thumbnail(url):
    try:
        if "watch?v=" in url:
            vid = url.split("watch?v=")[1].split("&")[0]
        elif "youtu.be/" in url:
            vid = url.split("youtu.be/")[1].split("?")[0]
        elif "shorts/" in url:
            vid = url.split("shorts/")[1].split("?")[0]
        else:
            return None
        return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg"
    except Exception:
        return None


def extract_channel(item):
    try:
        c = item.get("channel")
        if isinstance(c, dict):
            return c.get("name")
        return c
    except Exception:
        return None


def clean(d):
    return {k: v for k, v in d.items() if v is not None}


def format_duration(d):
    try:
        if isinstance(d, str):
            return d
        m, s = divmod(int(d), 60)
        return f"{m}:{str(s).zfill(2)}"
    except Exception:
        return "0:00"


def get_cache(key):
    data = STREAM_CACHE.get(key)
    if not data:
        return None
    stream, exp = data
    if time.time() > exp:
        STREAM_CACHE.pop(key, None)
        return None
    return stream


def set_cache(key, value):
    STREAM_CACHE[key] = (value, time.time() + CACHE_TTL)


async def safe_extract(extractor, url, cookies):
    for attempt in range(3):
        try:
            if inspect.iscoroutinefunction(extractor):
                return await extractor(url, cookies)
            return await asyncio.to_thread(extractor, url, cookies)
        except Exception:
            LOGGER.warning(f"[EXTRACT RETRY {attempt + 1}] {url}")
            await asyncio.sleep(1)
    return None


async def resolve(query, video=False, user_id=None):
    try:
        cookies = COOKIES_PATH if (COOKIES_PATH and os.path.exists(COOKIES_PATH)) else None
        extractor = get_video_stream if video else get_stream

        if PLAYLIST_REGEX.search(query):
            playlist = await _safe_call(get_playlist_songs, query)
            if not playlist:
                return None

            playlist = playlist[:20]

            tasks = [
                process(item, item.get("url"), extractor, cookies, video, user_id)
                for item in playlist
                if item.get("url")
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if r and not isinstance(r, Exception)]

        if YOUTUBE_REGEX.search(query):
            try:
                res = await _safe_call(Search, query, limit=1)
                if res and res.get("main_results"):
                    item = res["main_results"][0]
                    item["url"] = query
                else:
                    item = {"url": query, "title": "Unknown", "views": 0}
            except Exception:
                item = {"url": query, "title": "Unknown", "views": 0}

            result = await process(item, query, extractor, cookies, video, user_id)
            return [result] if result else None

        res = await _safe_call(Search, query, limit=1)
        if not res or not res.get("main_results"):
            return None

        item = res["main_results"][0]

        result = await process(item, item.get("url"), extractor, cookies, video, user_id)
        return [result] if result else None

    except Exception:
        LOGGER.error(f"[RESOLVE ERROR]\n{format_exc()}")
        return None


async def _safe_call(fn, *args, **kwargs):
    try:
        if inspect.iscoroutinefunction(fn):
            return await fn(*args, **kwargs)
        return await asyncio.to_thread(fn, *args, **kwargs)
    except Exception:
        LOGGER.error(f"[SAFE CALL ERROR] {fn.__name__}\n{format_exc()}")
        return None


async def process(item, url, extractor, cookies, video, user_id):
    try:
        if not url or not isinstance(url, str):
            return None

        key = f"{url}_{video}"

        stream = get_cache(key)

        if not stream:
            stream = await safe_extract(extractor, url, cookies)

            if not stream:
                stream = await safe_extract(extractor, url, None)

            if not stream or not isinstance(stream, str) or not stream.startswith("http"):
                LOGGER.error(f"[FINAL EXTRACT FAIL] {url}")
                return None

            set_cache(key, stream)

        return clean({
            "title": item.get("title"),
            "url": url,
            "duration": item.get("duration"),
            "duration_text": format_duration(item.get("duration")),
            "views": item.get("views") or 0,
            "channel": extract_channel(item),
            "thumb": item.get("thumbnail") or yt_thumbnail(url),
            "stream": stream,
            "is_video": video,
            "requested_by": {
                "id": user_id,
                "first_name": "User",
            },
        })

    except Exception:
        LOGGER.error(f"[PROCESS ERROR]\n{format_exc()}")
        return None


async def get_valid_stream(song):
    try:
        stream = song.get("stream")

        if stream and isinstance(stream, str) and stream.startswith("http"):
            return stream

        url = song.get("url")
        if not url:
            return None

        new = await resolve(
            query=url,
            video=song.get("is_video", False),
            user_id=(song.get("requested_by") or {}).get("id"),
        )

        if not new:
            return None

        first = next((x for x in new if x and isinstance(x, dict)), None)

        if not first or not first.get("stream"):
            return None

        stream = first["stream"]
        song["stream"] = stream

        set_cache(f"{url}_{song.get('is_video', False)}", stream)

        return stream

    except Exception:
        LOGGER.error(f"[GET_VALID_STREAM ERROR]\n{format_exc()}")
        return None
