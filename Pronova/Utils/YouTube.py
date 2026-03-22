import re
import os
import asyncio
import inspect
from traceback import format_exc

from YouTubeMusic.Search import Search
from YouTubeMusic.Stream import get_stream, get_video_stream
from YouTubeMusic.Playlist import get_playlist_songs

from Pronova.Database.YouTube import (
    get_stream_cache,
    set_stream_cache,
    is_stream_valid,
    get_search_cache,
    set_search_cache
)

from Pronova.Utils.Logger import LOGGER
from Config import COOKIES_PATH


PLAYLIST_REGEX = re.compile(r"(list=)")
YOUTUBE_REGEX = re.compile(r"(youtube\.com|youtu\.be|music\.youtube\.com)")


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
    except:
        return "0:00"


async def safe_extract(extractor, url, cookies):
    for _ in range(4):
        try:
            if inspect.iscoroutinefunction(extractor):
                return await extractor(url, cookies)
            return await asyncio.to_thread(extractor, url, cookies)
        except Exception:
            await asyncio.sleep(1)
    return None


async def resolve(query, video=False, user_id=None):
    try:
        LOGGER.info(f"[RESOLVE] {query}")

        cookies = COOKIES_PATH if (COOKIES_PATH and os.path.exists(COOKIES_PATH)) else None
        extractor = get_video_stream if video else get_stream

        if PLAYLIST_REGEX.search(query):
            key = f"playlist::{query}"

            cache = await get_search_cache(key)
            if cache:
                return cache

            playlist = await get_playlist_songs(query)
            if not playlist:
                return None

            playlist = playlist[:20]

            tasks = [
                process(item, item.get("url"), extractor, cookies, video, user_id)
                for item in playlist if item.get("url")
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)
            final = [r for r in results if r and not isinstance(r, Exception)]

            await set_search_cache(key, final)

            return final

        if YOUTUBE_REGEX.search(query):
            key = f"url::{query}"

            cache = await get_search_cache(key)
            if cache:
                return cache

            try:
                res = await Search(query, limit=1)

                if res and res.get("main_results"):
                    item = res["main_results"][0]

                    if item.get("url") and query not in item.get("url"):
                        item["url"] = query
                else:
                    item = {"url": query, "title": "Unknown"}

            except Exception:
                item = {"url": query, "title": "Unknown"}

            result = [
                await process(
                    item,
                    query,
                    extractor,
                    cookies,
                    video,
                    user_id
                )
            ]

            await set_search_cache(key, result)

            return result

        key = f"search::{query}"

        cache = await get_search_cache(key)
        if cache:
            return cache

        res = await Search(query, limit=1)

        if not res or not res.get("main_results"):
            return None

        item = res["main_results"][0]

        result = [
            await process(
                item,
                item.get("url"),
                extractor,
                cookies,
                video,
                user_id
            )
        ]

        await set_search_cache(key, result)

        return result

    except Exception:
        LOGGER.error(f"[RESOLVE ERROR]\n{format_exc()}")
        return None


async def process(item, url, extractor, cookies, video, user_id):
    try:
        key = f"{url}_{video}"

        stream = await get_stream_cache(key)

        if stream:
            if not await is_stream_valid(stream):
                stream = None

        if not stream:
            stream = await safe_extract(extractor, url, cookies)
            if not stream:
                return None
            await set_stream_cache(key, stream)

        return clean({
            "title": item.get("title"),
            "url": url,
            "duration": item.get("duration"),
            "duration_text": format_duration(item.get("duration")),
            "views": item.get("views"),
            "channel": extract_channel(item),
            "thumb": item.get("thumbnail") or yt_thumbnail(url),
            "stream": stream,
            "is_video": video,
            "requested_by": {
                "id": user_id,
                "first_name": "User"
            }
        })

    except Exception:
        LOGGER.error(f"[PROCESS ERROR]\n{format_exc()}")
        return None


async def get_valid_stream(song):
    try:
        if not await is_stream_valid(song["stream"]):
            new = await resolve(
                query=song["url"],
                video=song["is_video"],
                user_id=song["requested_by"]["id"]
            )

            if new:
                song["stream"] = new[0]["stream"]

        return song["stream"]

    except Exception:
        return song.get("stream")
