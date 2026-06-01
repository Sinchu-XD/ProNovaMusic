from traceback import format_exc
from Pronova.Utils.Logger import LOGGER
from . import Core


async def inc_song_play(chat_id: int, user_id: int, song_title: str):
    try:
        if not song_title:
            return

        title = song_title[:80]

        await Core.db.songs.update_one(
            {"title": title},
            {"$inc": {"plays": 1}},
            upsert=True,
        )

        from .Chats import inc_chat_song
        from .Users import inc_user_song

        try:
            await inc_chat_song(chat_id)
        except Exception:
            pass

        try:
            await inc_user_song(user_id)
        except Exception:
            pass

    except Exception:
        LOGGER.error(f"[INC SONG PLAY ERROR]\n{format_exc()}")


async def most_played(limit=5):
    try:
        results = []
        async for doc in Core.db.songs.find(
            {"plays": {"$gt": 0}},
            {"title": 1, "plays": 1},
        ).sort("plays", -1).limit(limit):
            results.append((doc["title"], doc["plays"]))
        return results
    except Exception:
        LOGGER.error(f"[MOST PLAYED ERROR]\n{format_exc()}")
        return []
